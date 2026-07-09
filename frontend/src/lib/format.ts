export function formatCurrency(value: string | number, currency = 'BRL'): string {
  const n = typeof value === 'string' ? Number(value) : value
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
  }).format(Number.isFinite(n) ? n : 0)
}

export function formatDate(iso: string): string {
  // Uma data "YYYY-MM-DD" deve ser lida no fuso LOCAL. `new Date("2026-07-01")`
  // é interpretado como meia-noite UTC e, em fusos negativos (Brasil, UTC-3),
  // exibiria o dia anterior (30/06). Montamos a data com os componentes locais.
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  const d = m
    ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
    : new Date(iso)
  return d.toLocaleDateString('pt-BR')
}
