/** Identifica o banco a partir do nome da conta e devolve rótulo + logo.
 * As conexões de sandbox trazem nomes como "BANCO DO BRASIL S/A", "OUROCARD…"
 * (BB), "Nu Pagamentos…" / "gold" (Nubank). Ao conectar bancos reais, o nome
 * da instituição também cai aqui. */
export interface Bank {
  key: string
  label: string
  logo: string
}

const BB: Bank = { key: 'bb', label: 'Banco do Brasil', logo: '/banks/bb.svg' }
const NUBANK: Bank = { key: 'nubank', label: 'Nubank', logo: '/banks/nubank.svg' }
const XP: Bank = { key: 'xp', label: 'XP Investimentos', logo: '/banks/xp.svg' }

export function bankOf(accountName: string | null | undefined): Bank | null {
  const n = (accountName ?? '').toLowerCase()
  if (n.includes('banco do brasil') || n.includes('ourocard') || /\bbb\b/.test(n))
    return BB
  if (n.includes('nubank') || n.includes('nu pagamentos') || n.includes('nu ') || n === 'gold')
    return NUBANK
  if (/\bxp\b/.test(n) || n.includes('xp investimentos')) return XP
  return null
}
