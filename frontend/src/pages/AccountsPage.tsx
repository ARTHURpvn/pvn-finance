import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { apiFetch } from '@/lib/api'
import { formatCurrency } from '@/lib/format'
import type { AccountsResponse, Account } from '@/lib/types'

const TYPE_LABEL: Record<Account['type'], string> = {
  checking: 'Conta corrente',
  savings: 'Poupança',
  payment: 'Conta de pagamento',
  credit_card: 'Cartão de crédito',
}

export function AccountsPage() {
  const [data, setData] = useState<AccountsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<AccountsResponse>('/accounts')
      .then(setData)
      .catch(() => toast.error('Falha ao carregar contas'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="text-muted-foreground">Carregando…</p>

  if (!data || data.accounts.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-muted-foreground">
          Nenhuma conta ainda. Conecte um banco em “Conexões” e sincronize.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Saldo em contas</CardDescription>
            <CardTitle className="text-2xl">
              {formatCurrency(data.summary.total)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Soma das contas, excluindo cartão de crédito.
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Cartão de crédito</CardDescription>
            <CardTitle className="text-2xl">
              {formatCurrency(data.summary.credit_card)}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            Passivo (fatura), reportado à parte.
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-3">Contas ({data.accounts.length})</h2>
        <div className="grid gap-3">
          {data.accounts.map((account) => (
            <Card key={account.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base">{account.name}</CardTitle>
                  <Badge variant="secondary" className="mt-1">
                    {TYPE_LABEL[account.type]}
                  </Badge>
                </div>
                <div className="text-right text-lg font-semibold">
                  {formatCurrency(account.balance, account.currency)}
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}
