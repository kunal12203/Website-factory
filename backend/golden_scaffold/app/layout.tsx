import type { Metadata } from 'next'
import './global.css'

export const metadata: Metadata = {
  title: 'My Website',
  description: 'Generated with AI Website Factory',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
