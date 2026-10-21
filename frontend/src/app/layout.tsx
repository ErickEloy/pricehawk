export const metadata = {
  title: 'PriceHawk - Monitor de Preços',
  description: 'Dashboard white-label para monitoramento de preços',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  )
}