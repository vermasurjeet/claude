import { Link, useLocation } from 'react-router-dom'
import { useHealth } from '../hooks/useStocks'

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/sectors', label: 'Sectors' },
]

export default function Layout({ children }) {
  const location = useLocation()
  const { data: health } = useHealth()

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-bold text-white">
              Stock Analyzer
            </Link>
            <nav className="flex gap-4">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                    location.pathname === item.path
                      ? 'bg-blue-600 text-white'
                      : 'text-slate-300 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4 text-sm text-slate-400">
            {health?.last_refresh && (
              <span>Last refresh: {new Date(health.last_refresh).toLocaleString()}</span>
            )}
            <span className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-green-400' : 'bg-red-400'}`} />
              {health?.stocks || 0} stocks
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {children}
      </main>
    </div>
  )
}
