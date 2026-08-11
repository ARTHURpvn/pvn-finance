import { describe, expect, it } from 'vitest'
import { formatCurrency, formatDate } from './format'

describe('formatCurrency', () => {
  it('formata valores em BRL', () => {
    expect(formatCurrency('59.9')).toContain('59,90')
    expect(formatCurrency(1000)).toContain('1.000,00')
  })

  it('trata entrada inválida como zero', () => {
    expect(formatCurrency('abc')).toContain('0,00')
  })
})

describe('formatDate', () => {
  it('lê YYYY-MM-DD no fuso local (não recua um dia)', () => {
    expect(formatDate('2026-07-01')).toBe('01/07/2026')
    expect(formatDate('2026-12-31')).toBe('31/12/2026')
  })
})
