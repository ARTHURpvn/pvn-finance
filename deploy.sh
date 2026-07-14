#!/usr/bin/env bash
#
# deploy.sh — sobe o Consolida (PVN Finance) em produção, do zero, num comando.
#
#   ./deploy.sh
#
# O que faz:
#   1. Confere pré-requisitos (docker + docker compose + openssl).
#   2. Cria o .env a partir do .env.example na primeira execução.
#   3. Gera segredos fortes (JWT_SECRET, VAULT_KEY, POSTGRES_PASSWORD) se ainda
#      forem os placeholders — e NÃO os regenera nas próximas execuções.
#   4. Configura HTTPS automático se você definir DOMAIN no .env.
#   5. Faz build e sobe db + api + worker + web (Caddy). Migrations rodam no boot.
#   6. Espera a API ficar saudável e mostra o status.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ENV_FILE=".env"
COMPOSE=(docker compose -f docker-compose.prod.yml)

c_green=$'\033[0;32m'; c_yellow=$'\033[0;33m'; c_red=$'\033[0;31m'
c_blue=$'\033[0;34m'; c_bold=$'\033[1m'; c_off=$'\033[0m'
info()  { printf '%s▸%s %s\n' "$c_blue" "$c_off" "$*"; }
ok()    { printf '%s✓%s %s\n' "$c_green" "$c_off" "$*"; }
warn()  { printf '%s!%s %s\n' "$c_yellow" "$c_off" "$*"; }
die()   { printf '%s✗ %s%s\n' "$c_red" "$*" "$c_off" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. Pré-requisitos
# ---------------------------------------------------------------------------
info "Conferindo pré-requisitos…"
command -v docker >/dev/null 2>&1 || die "docker não encontrado. Instale o Docker."
docker compose version >/dev/null 2>&1 || die "docker compose (v2) não encontrado."
command -v openssl >/dev/null 2>&1 || die "openssl não encontrado (necessário p/ gerar segredos)."
docker info >/dev/null 2>&1 || die "o daemon do Docker não está rodando (ou faltam permissões)."
ok "docker, docker compose e openssl prontos."

# ---------------------------------------------------------------------------
# Helpers de .env
# ---------------------------------------------------------------------------
get_env() { grep -E "^${1}=" "$ENV_FILE" 2>/dev/null | head -1 | cut -d= -f2- || true; }

set_env() {  # set_env CHAVE VALOR  (substitui a linha ou anexa; preserva '=' no valor)
  local key="$1" val="$2" tmp
  tmp="$(mktemp)"
  if grep -qE "^${key}=" "$ENV_FILE" 2>/dev/null; then
    awk -v k="$key" -v v="$val" '{ if (index($0, k"=")==1) print k"="v; else print }' \
      "$ENV_FILE" > "$tmp" && mv "$tmp" "$ENV_FILE"
  else
    rm -f "$tmp"; printf '%s=%s\n' "$key" "$val" >> "$ENV_FILE"
  fi
}

is_placeholder() {  # vazio ou um dos placeholders conhecidos do .env.example
  case "$1" in
    ""|change-me|troque-*|troque|CHANGE_ME|changeme|your-*) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# 2. .env
# ---------------------------------------------------------------------------
if [ ! -f "$ENV_FILE" ]; then
  [ -f ".env.example" ] || die ".env.example não encontrado."
  cp .env.example "$ENV_FILE"
  ok "Criei o .env a partir do .env.example."
else
  info ".env já existe — mantendo os valores atuais."
fi

# ---------------------------------------------------------------------------
# 3. Segredos (só gera se ainda for placeholder)
# ---------------------------------------------------------------------------
info "Conferindo segredos…"
if is_placeholder "$(get_env JWT_SECRET)"; then
  set_env JWT_SECRET "$(openssl rand -hex 32)"; ok "JWT_SECRET gerado."
else ok "JWT_SECRET já definido."; fi

if is_placeholder "$(get_env VAULT_KEY)"; then
  # Chave Fernet = base64 url-safe de 32 bytes.
  set_env VAULT_KEY "$(openssl rand -base64 32 | tr '+/' '-_')"; ok "VAULT_KEY (Fernet) gerada."
else ok "VAULT_KEY já definida."; fi

if is_placeholder "$(get_env POSTGRES_PASSWORD)"; then
  set_env POSTGRES_PASSWORD "$(openssl rand -hex 24)"; ok "POSTGRES_PASSWORD gerada."
else ok "POSTGRES_PASSWORD já definida."; fi

# APP_ENV de produção
set_env APP_ENV production

# ---------------------------------------------------------------------------
# 4. Domínio / HTTPS
# ---------------------------------------------------------------------------
DOMAIN="$(get_env DOMAIN)"
if [ -n "$DOMAIN" ]; then
  set_env SITE_ADDRESS "$DOMAIN"
  set_env CORS_ORIGINS "https://${DOMAIN}"
  ok "Domínio: ${DOMAIN} → Caddy vai emitir HTTPS automaticamente."
  warn "Garanta que o DNS de ${DOMAIN} aponta para este servidor e que as portas 80/443 estão abertas."
else
  set_env SITE_ADDRESS ":80"
  # A app proíbe CORS_ORIGINS='*' em produção. Como o Caddy serve front e API
  # na MESMA origem, o CORS nem é exercido em runtime — mas a guarda de boot
  # exige um valor concreto. Usa o IP do servidor.
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; ip="${ip:-localhost}"
  set_env CORS_ORIGINS "http://${ip}"
  warn "Sem DOMAIN no .env → servindo em HTTP na porta 80. Para HTTPS, defina DOMAIN=seu.dominio.com no .env e rode de novo."
fi

# Aviso (não bloqueia) se as credenciais do Pluggy estiverem vazias
if [ -z "$(get_env PLUGGY_CLIENT_ID)" ]; then
  warn "PLUGGY_CLIENT_ID/SECRET vazios no .env — a app sobe, mas não sincroniza bancos até você preencher."
fi

# ---------------------------------------------------------------------------
# 5. Build + up
# ---------------------------------------------------------------------------
info "Subindo a stack (build + up)… isso pode levar alguns minutos na 1ª vez."
"${COMPOSE[@]}" up -d --build

# ---------------------------------------------------------------------------
# 6. Health check
# ---------------------------------------------------------------------------
info "Esperando a API ficar saudável…"
api_cid="$("${COMPOSE[@]}" ps -q api)"
[ -n "$api_cid" ] || die "container da API não subiu. Veja: ${COMPOSE[*]} logs api"

healthy=""
for _ in $(seq 1 40); do
  status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' "$api_cid" 2>/dev/null || echo "")"
  if [ "$status" = "healthy" ]; then healthy=1; break; fi
  if [ "$status" = "unhealthy" ]; then break; fi
  sleep 3
done

echo
if [ -n "$healthy" ]; then
  ok "${c_bold}Deploy concluído.${c_off}"
else
  warn "A API ainda não reportou 'healthy'. Verifique os logs: ${COMPOSE[*]} logs -f api"
fi

"${COMPOSE[@]}" ps
echo
if [ -n "$DOMAIN" ]; then
  printf '%sAcesse:%s https://%s\n' "$c_bold" "$c_off" "$DOMAIN"
else
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"; ip="${ip:-localhost}"
  printf '%sAcesse:%s http://%s\n' "$c_bold" "$c_off" "$ip"
fi
echo "Logs:      ${COMPOSE[*]} logs -f"
echo "Derrubar:  ${COMPOSE[*]} down"
