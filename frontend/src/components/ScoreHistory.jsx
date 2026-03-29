import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

export default function ScoreHistory({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="text-slate-400 text-sm text-center py-8">
        No score history available yet.
      </div>
    )
  }

  const data = history.map((h) => ({
    date: new Date(h.computed_at).toLocaleDateString(),
    Total: h.total_score,
    Technical: h.technical_score,
    Fundamental: h.fundamental_score,
    Quantitative: h.quant_score,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
        <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569', borderRadius: '8px' }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        <Legend />
        <Line type="monotone" dataKey="Total" stroke="#f59e0b" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="Technical" stroke="#3b82f6" strokeWidth={1} dot={false} opacity={0.7} />
        <Line type="monotone" dataKey="Fundamental" stroke="#10b981" strokeWidth={1} dot={false} opacity={0.7} />
        <Line type="monotone" dataKey="Quantitative" stroke="#a855f7" strokeWidth={1} dot={false} opacity={0.7} />
      </LineChart>
    </ResponsiveContainer>
  )
}
