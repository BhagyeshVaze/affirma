import { signed, VERDICT_TEXT, worstVerdict } from '../format.js'

// Days (highs) and nights (lows) get separate verdicts. They are never combined.
function Part({ title, v, anomaly, unit }) {
  return (
    <div className="verdict-part">
      <h3>{title}</h3>
      <p className={`verdict-word v-${v.verdict}`}>{VERDICT_TEXT[v.verdict]}</p>
      <p>
        {v.unusual_days} of 7 outside the normal range
        {v.very_unusual_days > 0 && <> ({v.very_unusual_days} very unusual)</>}, average{' '}
        {signed(anomaly)}{unit} vs normal
      </p>
    </div>
  )
}

export default function VerdictBanner({ data }) {
  const { week, baseline, units, warnings } = data
  const t = units.temperature
  const overall = worstVerdict(week.highs.verdict, week.lows.verdict)
  return (
    <section className={`card verdict verdict-${overall}`}>
      <p className="eyebrow">This week vs {baseline.from_year} to {baseline.to_year}</p>
      <h2>
        Days: {VERDICT_TEXT[week.highs.verdict]}. Nights: {VERDICT_TEXT[week.lows.verdict]}.
      </h2>
      <div className="verdict-parts">
        <Part title="Days (highs)" v={week.highs} anomaly={week.avg_high_anomaly} unit={t} />
        <Part title="Nights (lows)" v={week.lows} anomaly={week.avg_low_anomaly} unit={t} />
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
