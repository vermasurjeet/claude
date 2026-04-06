import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'

export default function PriceChart({ prices }) {
  if (!prices || prices.length === 0) {
    return (
      <div className="text-slate-400 text-sm text-center py-12">
        No price data available.
      </div>
    )
  }

  const data = prices.map((p) => ({
    date: p.date,
    open: p.open,
    high: p.high,
    low: p.low,
    close: p.close,
    volume: p.volume,
  }))

  const formatPrice = (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
  const formatVol = (v) => {
    if (v >= 1e7) return `${(v / 1e7).toFixed(1)}Cr`
    if (v >= 1e5) return `${(v / 1e5).toFixed(1)}L`
    if (v >= 1e3) return `${(v / 1e3).toFixed(0)}K`
    return v
  }

  return (
    <div className="space-y-2">
      {/* Price chart */}
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="date"
            stroke="#94a3b8"
            tick={{ fontSize: 10 }}
            tickFormatter={(d) => {
              const date = new Date(d)
              return `${date.getDate()}/${date.getMonth() + 1}`
            }}
            interval={Math.floor(data.length / 8)}
          />
          <YAxis
            stroke="#94a3b8"
            tick={{ fontSize: 11 }}
            tickFormatter={formatPrice}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#e2e8f0', fontSize: 12 }}
            formatter={(value, name) => [formatPrice(value), name]}
            labelFormatter={(d) => new Date(d).toLocaleDateString('en-IN')}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            name="Close"
          />
          <Line
            type="monotone"
            dataKey="high"
            stroke="#22c55e"
            strokeWidth={1}
            dot={false}
            opacity={0.4}
            name="High"
          />
          <Line
            type="monotone"
            dataKey="low"
            stroke="#ef4444"
            strokeWidth={1}
            dot={false}
            opacity={0.4}
            name="Low"
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* Volume chart */}
      <ResponsiveContainer width="100%" height={100}>
        <ComposedChart data={data}>
          <XAxis dataKey="date" hide />
          <YAxis
            stroke="#94a3b8"
            tick={{ fontSize: 10 }}
            tickFormatter={formatVol}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #475569',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#e2e8f0', fontSize: 12 }}
            formatter={(value) => [formatVol(value), 'Volume']}
            labelFormatter={(d) => new Date(d).toLocaleDateString('en-IN')}
          />
          <Bar
            dataKey="volume"
            fill="#3b82f680"
            name="Volume"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
