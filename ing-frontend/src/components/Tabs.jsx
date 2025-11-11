export default function Tabs({ value, onChange, tabs }) {
    return (
      <div className="tabs">
        {tabs.map((t, i) => (
          <button
            key={t.value}
            className={`tab ${value === t.value ? "active" : ""}`}
            onClick={() => onChange(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>
    );
  }
  