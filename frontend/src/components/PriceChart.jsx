import { useEffect, useRef } from 'react'
import { createChart } from 'lightweight-charts'

export default function PriceChart({ prices }) {
  const chartRef = useRef(null)
  const chartInstance = useRef(null)

  useEffect(() => {
    if (!chartRef.current || !prices || prices.length === 0) return

    // Clear previous chart
    if (chartInstance.current) {
      chartInstance.current.remove()
    }

    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { color: '#1e293b' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#334155' },
        horzLines: { color: '#334155' },
      },
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: '#475569',
      },
      rightPriceScale: {
        borderColor: '#475569',
      },
    })

    // Candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#22c55e',
      wickDownColor: '#ef4444',
      wickUpColor: '#22c55e',
    })

    const candleData = prices.map((p) => ({
      time: p.date,
      open: p.open,
      high: p.high,
      low: p.low,
      close: p.close,
    }))

    candlestickSeries.setData(candleData)

    // Volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#3b82f6',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    })

    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    })

    const volumeData = prices.map((p) => ({
      time: p.date,
      value: p.volume,
      color: p.close >= p.open ? '#22c55e40' : '#ef444440',
    }))

    volumeSeries.setData(volumeData)

    chart.timeScale().fitContent()
    chartInstance.current = chart

    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
      if (chartRef.current) {
        chart.applyOptions({ width: chartRef.current.clientWidth })
      }
    })
    resizeObserver.observe(chartRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.remove()
    }
  }, [prices])

  return (
    <div
      ref={chartRef}
      className="w-full rounded-lg overflow-hidden bg-slate-800 border border-slate-700"
    />
  )
}
