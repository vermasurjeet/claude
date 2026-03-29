import { useState, useEffect } from 'react'

const SECTORS = [
  'All Sectors',
  'Technology',
  'Financial Services',
  'Consumer Staples',
  'Consumer Discretionary',
  'Energy',
  'Healthcare',
  'Industrials',
  'Materials',
  'Utilities',
  'Communication',
]

export default function Filters({ filters, onChange }) {
  const [search, setSearch] = useState(filters.search || '')

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      onChange({ ...filters, search: search || undefined })
    }, 300)
    return () => clearTimeout(timer)
  }, [search])

  return (
    <div className="flex flex-wrap gap-3 items-center bg-slate-800 rounded-lg p-4 border border-slate-700">
      {/* Search */}
      <input
        type="text"
        placeholder="Search stocks..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="bg-slate-900 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500 w-48"
      />

      {/* Sector dropdown */}
      <select
        value={filters.sector || ''}
        onChange={(e) => onChange({ ...filters, sector: e.target.value || undefined })}
        className="bg-slate-900 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
      >
        {SECTORS.map((s) => (
          <option key={s} value={s === 'All Sectors' ? '' : s}>
            {s}
          </option>
        ))}
      </select>

      {/* Min score */}
      <div className="flex items-center gap-2 text-sm">
        <label className="text-slate-400">Min Score:</label>
        <input
          type="number"
          min="0"
          max="100"
          value={filters.min_score ?? ''}
          onChange={(e) =>
            onChange({ ...filters, min_score: e.target.value ? Number(e.target.value) : undefined })
          }
          className="bg-slate-900 border border-slate-600 rounded px-2 py-1.5 text-sm text-white w-16 focus:outline-none focus:border-blue-500"
        />
      </div>

      {/* Sort */}
      <select
        value={filters.sort_by || 'score'}
        onChange={(e) => onChange({ ...filters, sort_by: e.target.value })}
        className="bg-slate-900 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
      >
        <option value="score">Sort by Score</option>
        <option value="name">Sort by Name</option>
        <option value="change">Sort by Change %</option>
      </select>
    </div>
  )
}
