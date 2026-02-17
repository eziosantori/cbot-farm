type MetricPoint = {
  label: string
  value: number
}

type BarChartProps = {
  title?: string
  points: MetricPoint[]
}

type TrendChartProps = {
  title?: string
  points: MetricPoint[]
}

function formatValue(value: number): string {
  const fixed = Math.abs(value) >= 100 ? value.toFixed(1) : value.toFixed(2)
  return `${fixed}`
}

export function MetricBarChart({ title, points }: BarChartProps): JSX.Element {
  if (!points.length) {
    return <p>No chart data available.</p>
  }

  const maxAbs = Math.max(...points.map((p) => Math.abs(p.value)), 1)

  return (
    <div className="card">
      {title ? <h3>{title}</h3> : null}
      <div className="bar-chart">
        {points.map((p) => {
          const width = Math.max((Math.abs(p.value) / maxAbs) * 100, 2)
          const tone = p.value >= 0 ? 'bar-positive' : 'bar-negative'
          return (
            <div className="bar-row" key={p.label}>
              <span className="bar-label">{p.label}</span>
              <div className="bar-track">
                <div className={`bar-fill ${tone}`} style={{ width: `${width}%` }} />
              </div>
              <span className="bar-value">{formatValue(p.value)}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function TrendChart({ title, points }: TrendChartProps): JSX.Element {
  if (points.length < 2) {
    return <p>No trend data available.</p>
  }

  const width = 680
  const height = 180
  const padding = 24
  const values = points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1

  const xy = points.map((p, idx) => {
    const x =
      padding +
      (idx / Math.max(points.length - 1, 1)) * (width - padding * 2)
    const y = padding + (1 - (p.value - min) / range) * (height - padding * 2)
    return { x, y, label: p.label, value: p.value }
  })

  const polyline = xy.map((p) => `${p.x},${p.y}`).join(' ')

  return (
    <div className="card">
      {title ? <h3>{title}</h3> : null}
      <svg
        className="trend-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={title || 'trend chart'}
      >
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          className="trend-axis"
        />
        <polyline points={polyline} className="trend-line" />
        {xy.map((p) => (
          <circle key={`${p.label}-${p.x}`} cx={p.x} cy={p.y} r="3" className="trend-point" />
        ))}
      </svg>
      <div className="trend-legend">
        <span>Min: {formatValue(min)}</span>
        <span>Max: {formatValue(max)}</span>
      </div>
    </div>
  )
}
