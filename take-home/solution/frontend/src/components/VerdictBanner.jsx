import { signed, VERDICT_TEXT } from '../format.js'

export default function VerdictBanner({ data }) {
  const { week, baseline, units, warnings } = data
  const t = units.temperature
  return (
    <section className={`card verdict verdict-${week.verdict}`}>
      <p className="eyebrow">This week vs {baseline.from_year} to {baseline.to_year}</p>
      <h2>{VERDICT_TEXT[week.verdict]}</h2>
      <p className="verdict-detail">
        <strong>{week.unusual_days} of 7</strong> days fall outside the normal range for their dates
        {week.very_unusual_days > 0 && <> ({week.very_unusual_days} very unusual)</>}.
      </p>
      <dl className="stats">
        <div>
          <dt>Highs vs normal</dt>
          <dd>{signed(week.avg_high_anomaly)}{t}</dd>
        </div>
        <div>
          <dt>Lows vs normal</dt>
          <dd>{signed(week.avg_low_anomaly)}{t}</dd>
        </div>
        <div>
          <dt>Baseline</dt>
          <dd>
            {baseline.years_used} years, ±{baseline.window_days} days
          </dd>
        </div>
      </dl>
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
