import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export default function Home() {
  return (
    <main className={inter.className}>
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="container mx-auto px-4 py-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            PriceHawk Dashboard
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Monitoramento de preços em tempo real
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-2">Total de Produtos</h3>
              <p className="text-3xl font-bold text-primary">0</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-2">Alertas Ativos</h3>
              <p className="text-3xl font-bold text-red-600">0</p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold mb-2">Economia Detectada</h3>
              <p className="text-3xl font-bold text-green-600">R$ 0,00</p>
            </div>
          </div>

          <div className="mt-8 bg-white rounded-lg shadow p-6">
            <h2 className="text-2xl font-semibold mb-4">Histórico de Preços</h2>
            <p className="text-gray-600">Gráfico será exibido aqui quando houver dados.</p>
          </div>
        </div>
      </div>
    </main>
  )
}