const YEAR_OPTIONS = [5, 10, 20, 30]

export function YearsSelect({ value, onChange }) {
  return (
    <div className="control">
      <label htmlFor="years">Compare with</label>
      <select id="years" value={value} onChange={(e) => onChange(Number(e.target.value))}>
        {YEAR_OPTIONS.map((y) => (
          <option key={y} value={y}>
            last {y} years
          </option>
        ))}
      </select>
    </div>
  )
}

export function Segmented({ label, value, options, onChange }) {
  return (
    <div className="control">
      <span className="control-label">{label}</span>
      <div className="segmented" role="group" aria-label={label}>
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            aria-pressed={value === o.value}
            onClick={() => onChange(o.value)}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}
