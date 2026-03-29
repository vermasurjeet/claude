import { useQuery } from '@tanstack/react-query'
import {
  fetchStocks,
  fetchStockDetail,
  fetchSectors,
  fetchTopStocks,
  fetchScoreHistory,
  fetchHealth,
} from '../api/client'

export function useStockList(params) {
  return useQuery({
    queryKey: ['stocks', params],
    queryFn: () => fetchStocks(params),
  })
}

export function useStockDetail(symbol) {
  return useQuery({
    queryKey: ['stock', symbol],
    queryFn: () => fetchStockDetail(symbol),
    enabled: !!symbol,
  })
}

export function useSectors() {
  return useQuery({
    queryKey: ['sectors'],
    queryFn: fetchSectors,
  })
}

export function useTopStocks(n = 20) {
  return useQuery({
    queryKey: ['topStocks', n],
    queryFn: () => fetchTopStocks(n),
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
    refetchInterval: 30000,
  })
}
