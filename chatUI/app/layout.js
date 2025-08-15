import './globals.css'

export const metadata = {
  title: 'Lumina - AI-Powered Business Intelligence',
  description: 'AI-powered chat interface for database queries and business intelligence',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="light">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
