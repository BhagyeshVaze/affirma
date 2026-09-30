import {
  Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { dayLabel, num, ordinal, signed } from '../format.js'
import LevelBadge from './LevelBadge.jsx'

// Forecast dots: hollow when normal; filled red (warm) or blue (cool) when unusual,
// bigger with a ring when very unusual. The table and tooltip repeat the level in words.
function LevelDot({ cx, cy, payload }) {
  if (cx == null || cy == null || payload.forecast == null) return null
  if (payload.level === 'normal' || payload.level === 'unknown') {
    return <circle cx={cx} cy={cy} r={4} fill="var(--surface)" stroke="var(--ink)" strokeWidth={2} />
  }
  const color = payload.direction === 'warmer' ? 'var(--warm)' : 'var(--cool)'
  const r = payload.level === 'very_unusual' ? 7 : 5.5
  return <circle cx={cx} cy={cy} r={r} fill={color} stroke="var(--surface)" strokeWidth={2} />
}

function ChartTooltip({ active, payload, unit }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="tooltip">
      <strong>{d.label}</strong>
      <div>Forecast: {num(d.forecast)}{unit}</div>
      <div>Normal: {num(d.normal)}{unit} ({signed(d.anomaly)}{unit})</div>
      <div>Normal range: {num(d.p5)} to {num(d.p95)}{unit}</div>
      {d.pct != null && <div>{ordinal(d.pct)} percentile of past values for these dates</div>}
      <LevelBadge level={d.level} direction={d.direction} />
    </div>
  )
}

export default function WeekChart({ data, measure }) {
  const unit = data.units.temperature
  const rows = data.days.map((d) => {
    const v = d[measure]
    return {
      label: dayLabel(d.date),
      band: v.p5 != null ? [v.p5, v.p95] : null,
      normal: v.normal, p5: v.p5, p95: v.p95, forecast: v.forecast,
      anomaly: v.anomaly, pct: v.pct_rank, level: v.level, direction: v.direction,
    }
  })

  return (
    <section className="card">
      <h3>Forecast {measure === 'high' ? 'highs' : 'lows'} vs the normal range</h3>
      <p className="legend">
        <span className="key key-band" /> Normal range (5th to 95th percentile)
        <span className="key key-normal" /> Average
        <span className="key key-forecast" /> Forecast
        <span className="key key-warm" /> Unusually warm
        <span className="key key-cool" /> Unusually cool
      </p>
      <div className="chart" style={{ height: 300 }}>
        <ResponsiveContainer>
          <ComposedChart data={rows} margin={{ top: 12, right: 16, bottom: 4, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--grid)" />
            <XAxis dataKey="label" tickLine={false} axisLine={{ stroke: 'var(--grid)' }} tick={{ fill: 'var(--text-2)', fontSize: 12 }} />
            <YAxis
              width={48}
              tickLine={false}
              axisLine={false}
              tick={{ fill: 'var(--text-2)', fontSize: 12 }}
              domain={['dataMin - 4', 'dataMax + 4']}
              allowDecimals={false}
              tickFormatter={(v) => `${Math.round(v)}°`}
            />
            <Tooltip content={<ChartTooltip unit={unit} />} cursor={{ stroke: 'var(--grid-strong)' }} />
            <Area dataKey="band" fill="var(--band)" stroke="none" isAnimationActive={false} activeDot={false} />
            <Line dataKey="normal" stroke="var(--text-2)" strokeWidth={1.5} strokeDasharray="4 4" dot={false} activeDot={false} isAnimationActive={false} />
            <Line dataKey="forecast" stroke="var(--ink)" strokeWidth={2} dot={<LevelDot />} activeDot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
