import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import { dark } from '@clerk/themes'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Doc2MCP - Intelligent Documentation Search for AI Agents',
  description: 'Transform any documentation into searchable knowledge for your AI assistants',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        variables: {
          colorPrimary: '#ef4444',
          colorBackground: '#0a0a0a',
          colorInputBackground: '#1a1a1a',
          colorInputText: '#ffffff',
        },
      }}
    >
      <html lang="en" className="dark">
        <body className={inter.className}>{children}</body>
      </html>
    </ClerkProvider>
  )
}
