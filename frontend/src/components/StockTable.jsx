import { useNavigate } from 'react-router-dom'
import ConvictionBadge from './ConvictionBadge'

export default function StockTable({ stocks, loading }) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 text-center text-slate-400">
        Loading stocks...
      </div>
    )
  }

  if (!stocks || stocks.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-8 text-center text-slate-400">
        No stocks found. Run a refresh to fetch data.
      </div>
    )
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-left">
              <th className="px-4 py-3 text-slate-300 font-medium">Symbol</th>
              <th className="px-4 py-3 text-slate-300 font-medium">Name</th>
              <th className="px-4 py-3 text-slate-300 font-medium">Sector</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-right">Price</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-right">Change %</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-center">Conviction</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-center">Tech</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-center">Fund</th>
              <th className="px-4 py-3 text-slate-300 font-medium text-center">Quant</th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((stock) => (
              <tr
                key={stock.symbol}
                onClick={() => navigate(`/stock/${stock.symbol}`)}
                className="border-b border-slate-700/50 hover:bg-slate-700/30 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 font-semibold text-white">{stock.symbol}</td>
                <td className="px-4 py-3 text-slate-300">{stock.name}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs">
                    {stock.sector}
                  </span>
                </td>
                <td className="px-4 py-3 text-right text-white font-mono">
                  {stock.last_price ? `₹${Number(stock.last_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                </td>
                <td className={`px-4 py-3 text-right font-mono ${
                  stock.change_pct > 0 ? 'text-green-400' : stock.change_pct < 0 ? 'text-red-400' : 'text-slate-400'
                }`}>
                  {stock.change_pct != null ? `${stock.change_pct > 0 ? '+' : ''}${stock.change_pct}%` : '—'}
                </td>
                <td className="px-4 py-3 text-center">
                  <ConvictionBadge score={stock.total_score} />
                </td>
                <td className="px-4 py-3 text-center text-slate-300">
                  {stock.technical_score?.toFixed(1) ?? '—'}
                </td>
                <td className="px-4 py-3 text-center text-slate-300">
                  {stock.fundamental_score?.toFixed(1) ?? '—'}
                </td>
                <td className="px-4 py-3 text-center text-slate-300">
                  {stock.quant_score?.toFixed(1) ?? '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
