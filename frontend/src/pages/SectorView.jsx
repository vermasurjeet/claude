import { useSectors } from '../hooks/useStocks'
import SectorHeatmap from '../components/SectorHeatmap'

export default function SectorView() {
  const { data, isLoading } = useSectors()

  if (isLoading) {
    return <div className="text-slate-400 text-center py-12">Loading sectors...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Sector Analysis</h1>
        <p className="text-slate-400 text-sm mt-1">
          Average conviction scores by sector
        </p>
      </div>
      <SectorHeatmap sectors={data?.sectors} />
    </div>
  )
}
