import { num } from '../format.js'

export default function RainCard({ data }) {
  const r = data.week.rain
  const unit = data.units.precipitation
  const digits = unit === 'in' ? 2 : 1
  return (
    <section className="card">
      <h3>Rain this week</h3>
      <dl className="stats">
        <div>
          <dt>Forecast total</dt>
          <dd>{num(r.forecast_total, digits)} {unit}</dd>
        </div>
        <div>
          <dt>Past average, same dates</dt>
          <dd>{num(r.avg_total, digits)} {unit}</dd>
        </div>
      </dl>
      {r.years_compared > 0 ? (
        <p className="note">
          Of {r.years_compared} past years, {r.years_wetter} were wetter and {r.years_drier} were drier
          over the same 7 dates.
        </p>
      ) : (
        <p className="note">Not enough rain data to compare.</p>
      )}
    </section>
  )
}
