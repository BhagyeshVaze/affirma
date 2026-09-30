import { signed, VERDICT_TEXT, worstVerdict } from '../format.js'

// Days (highs) and nights (lows) get separate verdicts. They are never combined.
function NotEnough({ v, total }) {
  if (v.days_without_forecast > 0) {
    return (
      <p>
        Only {v.days_judged} of {total} days can be judged: the forecast is missing values for{' '}
        {v.days_without_forecast} of {total} days. Try again later.
      </p>
    )
  }
  return (
    <p>
      Only {v.days_judged} of {total} days can be judged (5 are needed): there isn't enough past
      data for these dates. Try more years, or try again later.
    </p>
  )
}

function Part({ title, v, anomaly, unit, total }) {
  return (
    <div className="verdict-part">
      <h3>{title}</h3>
      <p className={`verdict-word v-${v.verdict}`}>{VERDICT_TEXT[v.verdict]}</p>
      {v.verdict === 'not_enough_history' ? (
        <NotEnough v={v} total={total} />
      ) : (
        <p>
          {v.unusual_days} of {total} outside the normal range
          {v.very_unusual_days > 0 && <> ({v.very_unusual_days} very unusual)</>}, average{' '}
          {signed(anomaly)}{unit} vs normal
        </p>
      )}
    </div>
  )
}

export default function VerdictBanner({ data }) {
  const { week, baseline, units, warnings } = data
  const t = units.temperature
  const total = data.days.length
  const overall = worstVerdict(week.highs.verdict, week.lows.verdict)
  return (
    <section className={`card verdict verdict-${overall}`}>
      <p className="eyebrow">This week vs {baseline.from_year} to {baseline.to_year}</p>
      <h2>
        Days: {VERDICT_TEXT[week.highs.verdict]}. Nights: {VERDICT_TEXT[week.lows.verdict]}.
      </h2>
      <div className="verdict-parts">
        <Part title="Days (highs)" v={week.highs} anomaly={week.avg_high_anomaly} unit={t} total={total} />
        <Part title="Nights (lows)" v={week.lows} anomaly={week.avg_low_anomaly} unit={t} total={total} />
        <div className="verdict-part">
          <h3>Baseline</h3>
          <p className="verdict-word">
            {baseline.years_used} years, ±{baseline.window_days} days
          </p>
          <p>A week is unusual when 3 or more days fall outside the 5th to 95th percentile.</p>
        </div>
      </div>
      {warnings.length > 0 && (
        <ul className="warnings">
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </section>
  )
}
