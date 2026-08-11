import { describe, expect, it } from 'vitest'
import { bankOf } from './banks'

describe('bankOf', () => {
  it('identifica Banco do Brasil por nome e cartão Ourocard', () => {
    expect(bankOf('BANCO DO BRASIL S/A')?.key).toBe('bb')
    expect(bankOf('OUROCARD PLATINUM VISA')?.key).toBe('bb')
    expect(bankOf('CDB BB Renda Fixa')?.key).toBe('bb')
  })

  it('identifica Nubank por Nu Pagamentos / gold', () => {
    expect(bankOf('Nu Pagamentos S.A.')?.key).toBe('nubank')
    expect(bankOf('gold')?.key).toBe('nubank')
    expect(bankOf('CDB - NU FINANCEIRA')?.key).toBe('nubank')
  })

  it('identifica XP Investimentos', () => {
    expect(bankOf('XP Investimentos')?.key).toBe('xp')
  })

  it('devolve null para desconhecido e entradas vazias', () => {
    expect(bankOf('Corretora Aleatória')).toBeNull()
    expect(bankOf(null)).toBeNull()
    expect(bankOf(undefined)).toBeNull()
  })

  it('cada banco traz rótulo e logo', () => {
    const bb = bankOf('Banco do Brasil')
    expect(bb?.label).toBe('Banco do Brasil')
    expect(bb?.logo).toMatch(/\/banks\/.+\.svg$/)
  })
})
