import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { EvolutionChart } from './EvolutionChart'

const fmt = (n: number) => `R$ ${n}`
const two = [
  { label: 'jun/2026', value: 5 },
  { label: 'jul/2026', value: 10 },
]

describe('EvolutionChart', () => {
  it('mostra estado vazio com menos de 2 pontos', () => {
    render(<EvolutionChart points={[{ label: 'jul', value: 10 }]} formatValue={fmt} gradientId="g1" />)
    expect(screen.getByText(/Sem histórico suficiente/i)).toBeInTheDocument()
  })

  it('desenha a linha com 2+ pontos', () => {
    const { container } = render(
      <EvolutionChart points={two} formatValue={fmt} gradientId="g2" />,
    )
    expect(container.querySelector('polyline')).not.toBeNull()
  })

  it('mostra tooltip (mês + valor) ao passar o mouse', () => {
    const { container } = render(
      <EvolutionChart points={two} formatValue={fmt} gradientId="g3" />,
    )
    const wrapper = container.firstElementChild as HTMLElement
    // jsdom não faz layout: forçamos uma largura para o cálculo do índice.
    wrapper.getBoundingClientRect = () =>
      ({ left: 0, width: 100, top: 0, right: 100, bottom: 0, height: 0, x: 0, y: 0, toJSON: () => ({}) }) as DOMRect
    fireEvent.mouseMove(wrapper, { clientX: 0 }) // frac 0 → primeiro ponto
    expect(screen.getByText('jun/2026')).toBeInTheDocument()
    expect(screen.getByText('R$ 5')).toBeInTheDocument()
  })
})
