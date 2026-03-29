import { useParams, Link } from 'react-router-dom'
import { useStockDetail } from '../hooks/useStocks'
import ConvictionBadge from '../components/ConvictionBadge'
import ScoreBreakdown from '../components/ScoreBreakdown'
import PriceChart from '../components/PriceChart'
import ScoreHistory from '../components/ScoreHistory'

export default function StockDetail() {
  const { symbol } = useParams()
  const { data, isLoading } = useStockDetail(symbol)

  if (isLoading) {
    return <div className="text-slate-400 text-center py-12">Loading {symbol}...</div>
  }

  if (!data || data.error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400">Stock not found: {symbol}</p>
        <Link to="/" className="text-blue-400 text-sm mt-2 inline-block">Back to Dashboard</Link>
      </div>
    )
  }

  const { stock, score, details, fundamentals, prices, score_history } = data

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/" className="text-blue-400 text-sm hover:underline">&larr; Back</Link>
          <h1 className="text-3xl font-bold text-white mt-1">{stock.symbol}</h1>
          <p className="text-slate-400">{stock.name}</p>
          <div className="flex gap-2 mt-2">
            <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs">{stock.sector}</span>
            <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-300 text-xs">{stock.industry}</span>
          </div>
        </div>
        <div className="text-right">
          <ConvictionBadge score={score?.total_score} size="lg" />
          {score?.computed_at && (
            <p className="text-slate-500 text-xs mt-1">
              Updated: {new Date(score.computed_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>

      {/* Score breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
            <h2 className="text-white font-semibold mb-3">Price Chart</h2>
            <PriceChart prices={prices} />
          </div>
        </div>
        <div className="space-y-4">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
            <h2 className="text-white font-semibold mb-3">Score Breakdown</h2>
            <ScoreBreakdown score={score} />
          </div>

          {/* Fundamental metrics */}
          {fundamentals && (
            <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
              <h2 className="text-white font-semibold mb-3">Fundamentals</h2>
              <div className="space-y-2 text-sm">
                <MetricRow label="P/E Ratio" value={fundamentals.pe_ratio} />
                <MetricRow label="P/B Ratio" value={fundamentals.pb_ratio} />
                <MetricRow label="ROE" value={fundamentals.roe} format="pct" />
                <MetricRow label="Debt/Equity" value={fundamentals.debt_to_equity} />
                <MetricRow label="EPS Growth" value={fundamentals.eps_growth} format="pct" />
                <MetricRow label="Revenue Growth" value={fundamentals.revenue_growth} format="pct" />
                <MetricRow label="Promoter %" value={fundamentals.promoter_holding} format="pct" />
                <MetricRow label="Div Yield" value={fundamentals.dividend_yield} format="pct" />
                {fundamentals.market_cap && (
                  <MetricRow
                    label="Market Cap"
                    value={`₹${(fundamentals.market_cap / 1e7).toFixed(0)} Cr`}
                    raw
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Factor detail */}
      {details && (
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
          <h2 className="text-white font-semibold mb-3">Factor Scores</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FactorGroup title="Technical" factors={details.technical} color="blue" />
            <FactorGroup title="Fundamental" factors={details.fundamental} color="emerald" />
            <FactorGroup title="Quantitative" factors={details.quantitative} color="purple" />
          </div>
        </div>
      )}

      {/* Score history */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h2 className="text-white font-semibold mb-3">Score History</h2>
        <ScoreHistory history={score_history} />
      </div>
    </div>
  )
}

function MetricRow({ label, value, format, raw }) {
  let display = '—'
  if (raw) {
    display = value
  } else if (value != null) {
    if (format === 'pct') {
      const pct = Math.abs(value) < 1 ? value * 100 : value
      display = `${pct.toFixed(1)}%`
    } else {
      display = Number(value).toFixed(2)
    }
  }

  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="text-white font-mono">{display}</span>
    </div>
  )
}

function FactorGroup({ title, factors, color }) {
  if (!factors) return null
  const colorMap = {
    blue: 'bg-blue-500',
    emerald: 'bg-emerald-500',
    purple: 'bg-purple-500',
  }

  return (
    <div>
      <h3 className="text-slate-300 font-medium mb-2">{title}</h3>
      <div className="space-y-2">
        {Object.entries(factors).map(([key, value]) => (
          <div key={key}>
            <div className="flex justify-between text-xs mb-0.5">
              <span className="text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
              <span className="text-slate-300">{value != null ? value.toFixed(1) : 'N/A'}</span>
            </div>
            <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${colorMap[color]}`}
                style={{ width: `${value ?? 0}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
