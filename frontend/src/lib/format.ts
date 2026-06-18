export function formatCurrency(value: string | number, currency = 'BRL'): string {
  const n = typeof value === 'string' ? Number(value) : value
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency,
  }).format(Number.isFinite(n) ? n : 0)
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('pt-BR')
}
