import { useNavigate } from 'react-router-dom'

function getScoreColor(score) {
  if (score >= 70) return 'from-green-900/60 to-green-800/30 border-green-700/50'
  if (score >= 50) return 'from-yellow-900/60 to-yellow-800/30 border-yellow-700/50'
  return 'from-red-900/60 to-red-800/30 border-red-700/50'
}

function getScoreTextColor(score) {
  if (score >= 70) return 'text-green-300'
  if (score >= 50) return 'text-yellow-300'
  return 'text-red-300'
}

export default function SectorHeatmap({ sectors }) {
  const navigate = useNavigate()

  if (!sectors || sectors.length === 0) {
    return (
      <div className="text-slate-400 text-center py-8">
        No sector data available. Run a refresh first.
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {sectors.map((sector) => (
        <div
          key={sector.sector}
          onClick={() => navigate(`/sectors?selected=${sector.sector}`)}
          className={`bg-gradient-to-br ${getScoreColor(sector.avg_score)} border rounded-lg p-4 cursor-pointer hover:scale-[1.02] transition-transform`}
        >
          <h3 className="text-white font-semibold text-lg">{sector.sector}</h3>
          <div className="mt-2 flex items-center justify-between">
            <span className={`text-2xl font-bold ${getScoreTextColor(sector.avg_score)}`}>
              {Number(sector.avg_score).toFixed(1)}
            </span>
            <span className="text-slate-400 text-sm">
              {sector.stock_count} stocks
            </span>
          </div>
          {sector.top_symbol && (
            <div className="mt-2 text-sm text-slate-300">
              Top: <span className="text-white font-medium">{sector.top_symbol}</span>
              {' '}({Number(sector.top_score).toFixed(1)})
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
