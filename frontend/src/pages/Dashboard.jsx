import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useStockList } from '../hooks/useStocks'
import StockTable from '../components/StockTable'
import Filters from '../components/Filters'
import { triggerRefresh } from '../api/client'

export default function Dashboard() {
  const [filters, setFilters] = useState({
    sort_by: 'score',
    order: 'desc',
    limit: 50,
  })

  const { data, isLoading } = useStockList(filters)
  const refreshMutation = useMutation({ mutationFn: triggerRefresh })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Stock Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">
            {data?.total ?? 0} stocks tracked
          </p>
        </div>
        <button
          onClick={() => refreshMutation.mutate()}
          disabled={refreshMutation.isPending}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:text-blue-300 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Scores'}
        </button>
      </div>

      {refreshMutation.isSuccess && (
        <div className="bg-green-900/30 border border-green-700/50 text-green-300 px-4 py-2 rounded-lg text-sm">
          Refresh started. Scores will update in a few minutes.
        </div>
      )}

      <Filters filters={filters} onChange={setFilters} />
      <StockTable stocks={data?.stocks} loading={isLoading} />

      {/* Pagination */}
      {data?.total > filters.limit && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setFilters(f => ({ ...f, offset: Math.max(0, (f.offset || 0) - f.limit) }))}
            disabled={!filters.offset}
            className="px-3 py-1 rounded bg-slate-700 text-slate-300 text-sm disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-3 py-1 text-slate-400 text-sm">
            {(filters.offset || 0) + 1}–{Math.min((filters.offset || 0) + filters.limit, data.total)} of {data.total}
          </span>
          <button
            onClick={() => setFilters(f => ({ ...f, offset: (f.offset || 0) + f.limit }))}
            disabled={(filters.offset || 0) + filters.limit >= data.total}
            className="px-3 py-1 rounded bg-slate-700 text-slate-300 text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
