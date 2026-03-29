export default function ConvictionBadge({ score, size = 'md' }) {
  if (score == null) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-400">
        N/A
      </span>
    )
  }

  let colorClass
  if (score >= 70) {
    colorClass = 'bg-green-900/50 text-green-300 border-green-700'
  } else if (score >= 50) {
    colorClass = 'bg-yellow-900/50 text-yellow-300 border-yellow-700'
  } else {
    colorClass = 'bg-red-900/50 text-red-300 border-red-700'
  }

  const sizeClass = size === 'lg'
    ? 'px-3 py-1 text-lg font-bold'
    : 'px-2 py-0.5 text-sm font-semibold'

  return (
    <span className={`inline-flex items-center rounded border ${colorClass} ${sizeClass}`}>
      {score.toFixed(1)}
    </span>
  )
}
