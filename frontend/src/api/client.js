import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

export const fetchStocks = (params) => api.get('/stocks', { params }).then(r => r.data)
export const fetchStockDetail = (symbol) => api.get(`/stocks/${symbol}`).then(r => r.data)
export const fetchSectors = () => api.get('/sectors').then(r => r.data)
export const fetchSectorDetail = (sector) => api.get(`/sectors/${sector}`).then(r => r.data)
export const fetchTopStocks = (n = 20) => api.get('/scores/top', { params: { n } }).then(r => r.data)
export const fetchScoreHistory = (symbol, days = 90) =>
  api.get(`/scores/history/${symbol}`, { params: { days } }).then(r => r.data)
export const fetchScoreChanges = (days = 7) =>
  api.get('/scores/changes', { params: { days } }).then(r => r.data)
export const triggerRefresh = () => api.post('/refresh').then(r => r.data)
export const fetchRefreshStatus = () => api.get('/refresh/status').then(r => r.data)
export const fetchHealth = () => api.get('/health').then(r => r.data)

export default api
