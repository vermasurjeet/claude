import { useQuery } from '@tanstack/react-query'
import {
  fetchStocks,
  fetchStockDetail,
  fetchSectors,
  fetchTopStocks,
  fetchScoreHistory,
  fetchHealth,
} from '../api/client'

// Auto-refresh stocks every 30s when market is open, 5min when closed
export function useStockList(params) {
  const { data: health } = useHealth()
  const interval = health?.market_open ? 30_000 : 5 * 60_000

  return useQuery({
    queryKey: ['stocks', params],
    queryFn: () => fetchStocks(params),
    refetchInterval: interval,
  })
}

export function useStockDetail(symbol) {
  const { data: health } = useHealth()
  const interval = health?.market_open ? 30_000 : 5 * 60_000

  return useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol),
    enabled: !!symbol,
    refetchInterval: interval,
  })
}

export function useSectors() {
  return useQuery({
    queryKey: ['sectors'],
    queryFn: fetchSectors,
    refetchInterval: 60_000,
  })
}

export function useTopStocks(n = 20) {
  const { data: health } = useHealth()
  const interval = health?.market_open ? 30_000 : 5 * 60_000

  return useQuery({
    queryKey: ['topStocks', n],
    queryFn: () => fetchTopStocks(n),
    refetchInterval: interval,
  })
}

export function useScoreHistory(symbol, days = 90) {
  return useQuery({
    queryKey: ['scoreHistory', symbol, days],
    queryFn: () => fetchScoreHistory(symbol, days),
    enabled: !!symbol,
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 15_000,
  })
}
