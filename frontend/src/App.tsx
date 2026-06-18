import { Button } from '@/components/ui/button'

function App() {
  return (
    <main className="min-h-svh flex flex-col items-center justify-center gap-6 p-8">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">Consolida</h1>
        <p className="text-muted-foreground">
          Agregador financeiro pessoal — bootstrap (F1) com shadcn/ui.
        </p>
      </div>
      <div className="flex gap-3">
        <Button>Conectar banco</Button>
        <Button variant="outline">Ver dashboard</Button>
      </div>
    </main>
  )
}

export default App
