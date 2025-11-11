export default function Section({ title, children, count }) {
    return (
      <section className="section">
        <div className="section-header">
          <h2>{title}</h2>
          {typeof count === "number" && <span className="badge">{count}</span>}
        </div>
        <div>{children}</div>
      </section>
    );
  }
  