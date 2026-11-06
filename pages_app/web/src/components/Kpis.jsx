export default function Kpis({ scan }) {
  if (!scan) return null;
  const avg = scan.rows.length
    ? scan.rows.reduce((s, r) => s + Number(r["200 DMA Dist %"]), 0) / scan.rows.length
    : null;
  const rate = scan.total ? ((scan.count / scan.total) * 100).toFixed(1) + "%" : "0%";
  const items = [
    ["Stocks scanned", scan.total, ""],
    ["Positive breakouts", scan.count, "accent"],
    ["Hit rate", rate, ""],
    ["Avg. distance from 200 DMA", avg === null ? "\u2013" : avg.toFixed(2) + "%", ""],
  ];
  return (
    <section className="kpis">
      {items.map(([label, value, cls]) => (
        <div key={label} className={"kpi " + cls}>
          <span className="kpi-label">{label}</span>
          <span className="kpi-value">{value}</span>
        </div>
      ))}
    </section>
  );
}
