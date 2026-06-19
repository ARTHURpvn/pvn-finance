import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { formatCurrency } from './format'

interface UiContextValue {
  hideValues: boolean
  toggleHide: () => void
  money: (value: string | number, currency?: string) => string
}

const UiContext = createContext<UiContextValue | null>(null)

export function UiProvider({ children }: { children: ReactNode }) {
  const [hideValues, setHideValues] = useState(false)
  const toggleHide = useCallback(() => setHideValues((v) => !v), [])
  const money = useCallback(
    (value: string | number, currency = 'BRL') =>
      hideValues ? 'R$ ••••' : formatCurrency(value, currency),
    [hideValues],
  )
  const value = useMemo(
    () => ({ hideValues, toggleHide, money }),
    [hideValues, toggleHide, money],
  )
  return <UiContext value={value}>{children}</UiContext>
}

export function useUi(): UiContextValue {
  const ctx = useContext(UiContext)
  if (!ctx) throw new Error('useUi deve ser usado dentro de UiProvider')
  return ctx
}
