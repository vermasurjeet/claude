const categories = [
  { key: 'technical_score', label: 'Technical', color: 'bg-blue-500' },
  { key: 'fundamental_score', label: 'Fundamental', color: 'bg-emerald-500' },
  { key: 'quant_score', label: 'Quantitative', color: 'bg-purple-500' },
]

export default function ScoreBreakdown({ score }) {
  if (!score) return null

  return (
    <div className="space-y-3">
      {categories.map(({ key, label, color }) => {
        const value = score[key] ?? 0
        return (
          <div key={key}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-300">{label}</span>
              <span className="text-white font-medium">{value.toFixed(1)}</span>
            </div>
            <div className="h-2.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${color}`}
                style={{ width: `${value}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
