import {
  Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { num, ordinal, shortDate, signed } from '../format.js'
import { Empty, ErrorState, Loading } from './States.jsx'

function ChartTooltip({ active, payload, unit }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="tooltip">
      <strong>
        {shortDate(d.start)} to {shortDate(d.end)}, {d.year}
        {d.is_forecast && ' (forecast)'}
      </strong>
      <div>Average high: {num(d.avg_high)}{unit}</div>
      <div>Average low: {num(d.avg_low)}{unit}</div>
      <div>Days with data: {d.days_with_data} of 7</div>
    </div>
  )
}

export default function SameWeekChart({ request }) {
  if (request.status === 'loading') return <Loading label="Loading past years" height={320} />
  if (request.status === 'error') return <ErrorState error={request.error} onRetry={request.retry} />
  if (request.status !== 'success') return null

  const data = request.data
  const unit = data.units.temperature
  const rows = data.years.filter((r) => r.avg_high != null)
  // the backend's past average, so the line matches the sentence
  const { rank_warmest: rank, out_of: outOf, vs_past_mean: diff, past_avg_high: pastMean } = data.this_week

  return (
    <section className="card">
      <h3>The same week in past years</h3>
      {rank != null ? (
        <p className="headline-small">
          This week's average high ranks <strong>{rank === 1 ? 'warmest' : `${ordinal(rank)} warmest`}</strong> of {outOf} weeks
          ({signed(diff)}{unit} vs the past average).
        </p>
      ) : (
        <p className="note">Not enough forecast data to rank this week.</p>
      )}
      {rows.length === 0 ? (
        <Empty title="No past data for these dates." />
      ) : (
        <div className="chart" style={{ height: 260 }}>
          <ResponsiveContainer>
            <BarChart data={rows} margin={{ top: 12, right: 16, bottom: 4, left: 0 }} barCategoryGap="20%">
              <CartesianGrid vertical={false} stroke="var(--grid)" />
              <XAxis dataKey="year" tickLine={false} axisLine={{ stroke: 'var(--grid)' }} tick={{ fill: 'var(--text-2)', fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis
                width={48}
                tickLine={false}
                axisLine={false}
                tick={{ fill: 'var(--text-2)', fontSize: 12 }}
                domain={['dataMin - 5', 'dataMax + 3']}
                allowDecimals={false}
                tickFormatter={(v) => `${Math.round(v)}°`}
              />
              <Tooltip content={<ChartTooltip unit={unit} />} cursor={{ fill: 'var(--hover)' }} />
              {pastMean != null && (
                <ReferenceLine y={pastMean} stroke="var(--text-2)" strokeDasharray="4 4"
                  label={{ value: 'past average', position: 'insideTopLeft', fill: 'var(--text-2)', fontSize: 11 }} />
              )}
              <Bar dataKey="avg_high" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                {rows.map((r) => (
                  <Cell key={r.year} fill={r.is_forecast ? 'var(--accent)' : 'var(--bar)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="legend">
        <span className="key key-bar" /> Past years (average high)
        <span className="key key-accent" /> This week (forecast)
      </p>
    </section>
  )
}
