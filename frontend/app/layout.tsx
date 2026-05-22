import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title:       'Poker AI',
  description: 'Poker AI training dashboard',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-gray-100 min-h-screen antialiased">
        <nav className="border-b border-gray-800 px-6 py-4">
          <a href="/" className="text-emerald-400 font-bold text-xl tracking-tight">
            ♠ Poker AI
          </a>
        </nav>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  )
}
