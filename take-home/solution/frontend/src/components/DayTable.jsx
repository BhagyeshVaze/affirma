import { dayLabel, num, ordinal, signed } from '../format.js'
import LevelBadge from './LevelBadge.jsx'

function Cell({ v, unit }) {
  return (
    <>
      <td className="num">{num(v.forecast)}{unit}</td>
      <td className="num muted">{num(v.normal)}{unit}</td>
      <td className="num">{signed(v.anomaly)}</td>
      <td className="num muted">{v.pct_rank == null ? 'n/a' : ordinal(v.pct_rank)}</td>
      <td><LevelBadge level={v.level} direction={v.direction} /></td>
    </>
  )
}

export default function DayTable({ data }) {
  const unit = data.units.temperature
  return (
    <section className="card">
      <h3>Day by day</h3>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th rowSpan={2}>Day</th>
              <th colSpan={5} className="group">High</th>
              <th colSpan={5} className="group">Low</th>
            </tr>
            <tr>
              {['high', 'low'].map((k) => (
                <FragmentHeaders key={k} />
              ))}
            </tr>
          </thead>
          <tbody>
            {data.days.map((d) => (
              <tr key={d.date}>
                <th scope="row">{dayLabel(d.date)}</th>
                <Cell v={d.high} unit={unit} />
                <Cell v={d.low} unit={unit} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="note">Percentile: where the forecast falls among past values for the same dates (50th is typical).</p>
    </section>
  )
}

function FragmentHeaders() {
  return (
    <>
      <th className="num">Forecast</th>
      <th className="num">Normal</th>
      <th className="num">Diff</th>
      <th className="num">Pct.</th>
      <th>Level</th>
    </>
  )
}
