import { useEffect, useMemo, useState } from 'react'
import client from '../api/client'

const PERIODS = [
  { value: '1m', label: '1 Month' },
  { value: '6m', label: '6 Months' },
  { value: '1y', label: '1 Year' }
]

function formatAxisDate(value) {
  const date = new Date(value)
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date)
}

function buildLinePath(points, width, height, padding) {
  if (points.length === 0) return ''
  const xs = points.map((_, index) => padding.left + (index * (width - padding.left - padding.right)) / Math.max(points.length - 1, 1))
  const ys = points.map((point) => point.y)
  return points
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${xs[index]} ${ys[index]}`)
    .join(' ')
}

function buildAreaPath(points, width, height, padding) {
  if (points.length === 0) return ''
  const top = buildLinePath(points, width, height, padding)
  const lastX = padding.left + ((points.length - 1) * (width - padding.left - padding.right)) / Math.max(points.length - 1, 1)
  const firstX = padding.left
  const baseline = height - padding.bottom
  return `${top} L ${lastX} ${baseline} L ${firstX} ${baseline} Z`
}

function goldColor(delta) {
  if (delta > 0) return '#4ade80'
  if (delta < 0) return '#fb7185'
  return '#d8b15a'
}

export default function Dashboard() {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [latest, setLatest] = useState(null)
  const [period, setPeriod] = useState('1m')
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [predRes, latestRes] = await Promise.all([
          client.get('/predictions/next-5-days'),
          client.get('/market/latest')
        ])
        setPredictions(predRes.data.predictions)
        setLatest(latestRes.data)
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    const loadHistory = async () => {
      try {
        setHistoryLoading(true)
        setHistoryError('')
        const { data } = await client.get('/market/history', { params: { period } })
        setHistory(data.points || [])
      } catch (err) {
        setHistoryError(err?.response?.data?.detail || 'Unable to load market history')
        setHistory([])
      } finally {
        setHistoryLoading(false)
      }
    }
    loadHistory()
  }, [period])

  const chartData = useMemo(() => {
    const width = 1000
    const height = 320
    const padding = { top: 24, right: 20, bottom: 56, left: 84 }
    if (history.length === 0) {
      return {
        width,
        height,
        padding,
        points: [],
        line: '',
        area: '',
        min: 0,
        max: 0,
        latestPoint: null,
        yTicks: [],
        xTicks: []
      }
    }

    const values = history.map((item) => Number(item.gold_price))
    const min = Math.min(...values)
    const max = Math.max(...values)
    const spread = Math.max(max - min, max * 0.02 || 1)
    const points = history.map((item, index) => {
      const x = padding.left + (index * (width - padding.left - padding.right)) / Math.max(history.length - 1, 1)
      const normalized = (Number(item.gold_price) - min) / spread
      const y = height - padding.bottom - normalized * (height - padding.top - padding.bottom)
      return { ...item, x, y }
    })

    const yTicks = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4
      const value = max - (max - min) * ratio
      const y = padding.top + ratio * (height - padding.top - padding.bottom)
      return { value, y }
    })

    const tickIndexes = Array.from(
      new Set([
        0,
        Math.round((history.length - 1) * 0.25),
        Math.round((history.length - 1) * 0.5),
        Math.round((history.length - 1) * 0.75),
        history.length - 1
      ])
    )
      .filter((index) => index >= 0 && index < history.length)
      .map((index) => ({
        index,
        label: formatAxisDate(history[index].market_date),
        x: points[index].x
      }))

    const line = buildLinePath(points, width, height, padding)
    const area = buildAreaPath(points, width, height, padding)
    return {
      width,
      height,
      padding,
      points,
      line,
      area,
      min,
      max,
      latestPoint: points[points.length - 1],
      yTicks,
      xTicks: tickIndexes
    }
  }, [history])

  const latestPrice = latest ? Number(latest.gold_price) : null
  const firstPrice = history.length > 0 ? Number(history[0].gold_price) : null
  const delta = latestPrice !== null && firstPrice !== null ? latestPrice - firstPrice : 0
  const deltaColor = goldColor(delta)

  const recommendation = useMemo(() => {
    if (!predictions.length) return null

    const totals = predictions.reduce(
      (acc, item) => {
        acc.up += Number(item.up_probability || 0)
        acc.down += Number(item.down_probability || 0)
        return acc
      },
      { up: 0, down: 0 }
    )

    const averageUp = totals.up / predictions.length
    const averageDown = totals.down / predictions.length

    if (averageUp >= 55) {
      return {
        label: 'BUY',
        tone: 'buy',
        message: 'Average UP probability is strong enough to favor buying.'
      }
    }

    if (averageDown >= 55) {
      return {
        label: 'SELL',
        tone: 'sell',
        message: 'Average DOWN probability is strong enough to favor selling.'
      }
    }

    return {
      label: 'HOLD',
      tone: 'hold',
      message: 'Neither direction is strong enough, so waiting is the safer call.'
    }
  }, [predictions])

  return (
    <main className="content-grid">
      <section className="panel panel-wide">
        <div className="section-head">
          <div>
            <p className="eyebrow">AI dashboard</p>
            <h2>Gold trend and next 5-day direction forecast</h2>
          </div>
          {latest && (
            <div className="market-chip">
              Latest market snapshot: {latest.market_date}
            </div>
          )}
        </div>

        <div className="trend-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">Market trend</p>
              <h3>Gold price history</h3>
            </div>
            <div className="period-switcher">
              {PERIODS.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  className={item.value === period ? 'period-btn active' : 'period-btn'}
                  onClick={() => setPeriod(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          {historyLoading && <p className="muted">Loading market history...</p>}
          {historyError && <div className="error-box">{historyError}</div>}

          {!historyLoading && history.length > 0 && (
            <div className="chart-shell">
              <div className="chart-meta">
                <div>
                  <span className="chart-label">Latest price</span>
                  <strong>${latestPrice?.toFixed(2)}</strong>
                </div>
                <div>
                  <span className="chart-label">Change over period</span>
                  <strong style={{ color: deltaColor }}>
                    {delta >= 0 ? '+' : ''}
                    {delta.toFixed(2)}
                  </strong>
                </div>
                <div>
                  <span className="chart-label">Range</span>
                  <strong>${chartData.min.toFixed(2)} - ${chartData.max.toFixed(2)}</strong>
                </div>
              </div>

              <svg
                className="trend-chart"
                viewBox={`0 0 ${chartData.width} ${chartData.height}`}
                role="img"
                aria-label="Gold price history chart"
              >
                <defs>
                  <linearGradient id="goldLine" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f4d98b" stopOpacity="0.95" />
                    <stop offset="100%" stopColor="#b8862e" stopOpacity="0.95" />
                  </linearGradient>
                  <linearGradient id="goldArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f4d98b" stopOpacity="0.28" />
                    <stop offset="100%" stopColor="#f4d98b" stopOpacity="0.02" />
                  </linearGradient>
                </defs>

                <line
                  x1={chartData.padding.left}
                  y1={chartData.height - chartData.padding.bottom}
                  x2={chartData.width - chartData.padding.right}
                  y2={chartData.height - chartData.padding.bottom}
                  className="chart-axis"
                />
                <line
                  x1={chartData.padding.left}
                  y1={chartData.padding.top}
                  x2={chartData.padding.left}
                  y2={chartData.height - chartData.padding.bottom}
                  className="chart-axis"
                />

                {chartData.yTicks.map((tick) => (
                  <g key={tick.value}>
                    <line
                      x1={chartData.padding.left}
                      y1={tick.y}
                      x2={chartData.width - chartData.padding.right}
                      y2={tick.y}
                      className="chart-grid"
                    />
                    <text
                      x={chartData.padding.left - 12}
                      y={tick.y + 4}
                      textAnchor="end"
                      className="chart-tick chart-y-tick"
                    >
                      ${tick.value.toFixed(2)}
                    </text>
                  </g>
                ))}

                <path d={chartData.area} fill="url(#goldArea)" />
                <path d={chartData.line} fill="none" stroke="url(#goldLine)" strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />

                {chartData.points.map((point, index) => (
                  <g key={`${point.market_date}-${index}`} className="chart-hit-area">
                    <circle
                      cx={point.x}
                      cy={point.y}
                      r="10"
                      fill="transparent"
                      stroke="transparent"
                      pointerEvents="all"
                    >
                      <title>
                        {`${formatAxisDate(point.market_date)} - $${Number(point.gold_price).toFixed(2)}`}
                      </title>
                    </circle>
                    {chartData.xTicks.some((tick) => tick.index === index) ? (
                      <text
                        x={point.x}
                        y={chartData.height - 18}
                        textAnchor="middle"
                        className="chart-tick chart-x-tick"
                      >
                        {formatAxisDate(point.market_date)}
                      </text>
                    ) : null}
                  </g>
                ))}

                {chartData.latestPoint && (
                  <g>
                    <line
                      x1={chartData.latestPoint.x}
                      y1={chartData.latestPoint.y}
                      x2={chartData.latestPoint.x}
                      y2={chartData.height - chartData.padding.bottom}
                      stroke={deltaColor}
                      strokeDasharray="6 6"
                      opacity="0.35"
                    />
                    <circle cx={chartData.latestPoint.x} cy={chartData.latestPoint.y} r="7" fill={deltaColor} />
                  </g>
                )}
              </svg>
            </div>
          )}
        </div>

        <div className="section-head forecast-head">
          <div>
            <p className="eyebrow">Forecast</p>
            <h2>Next 5-day gold direction forecast</h2>
          </div>
          {latest && (
            <div className="market-chip">
              Latest market snapshot: {latest.market_date}
            </div>
          )}
        </div>

        {loading && <p className="muted">Loading predictions...</p>}
        {error && <div className="error-box">{error}</div>}

        {recommendation && (
          <div className={`recommendation-card recommendation-${recommendation.tone}`}>
            <div>
              <p className="eyebrow">AI recommendation</p>
              <h3>{recommendation.label}</h3>
              <p className="muted recommendation-copy">{recommendation.message}</p>
            </div>
            <div className="recommendation-stats">
              <div>
                <span>Average UP</span>
                <strong>
                  {(
                    predictions.reduce((sum, item) => sum + Number(item.up_probability || 0), 0) /
                    Math.max(predictions.length, 1)
                  ).toFixed(2)}
                  %
                </strong>
              </div>
              <div>
                <span>Average DOWN</span>
                <strong>
                  {(
                    predictions.reduce((sum, item) => sum + Number(item.down_probability || 0), 0) /
                    Math.max(predictions.length, 1)
                  ).toFixed(2)}
                  %
                </strong>
              </div>
            </div>
          </div>
        )}

        <div className="compact-note">
          <strong>Note:</strong> This AI insight is for information only and is not financial advice.
          Markets are volatile, so please do your own research before acting.
        </div>

        <div className="prediction-grid">
          {predictions.map((item) => (
            <article className="prediction-card" key={item.date}>
              <span className="prediction-date">{item.date}</span>
              <div className={`prediction-direction ${item.direction === 'UP' ? 'positive' : 'negative'}`}>
                {item.direction}
              </div>
              <div className="prob-row">
                <span>UP</span>
                <strong>{item.up_probability.toFixed(2)}%</strong>
              </div>
              <div className="prob-row">
                <span>DOWN</span>
                <strong>{item.down_probability.toFixed(2)}%</strong>
              </div>
            </article>
          ))}
        </div>
      </section>

      <aside className="panel panel-side">
        <p className="eyebrow">Model note</p>
        <h3>Direction first, not exact price.</h3>
        <p className="muted">
          The backend keeps the existing linear-regression approach from your provided code,
          then converts the forecast into UP and DOWN probabilities for the next 5 calendar days.
        </p>
      </aside>
    </main>
  )
}
