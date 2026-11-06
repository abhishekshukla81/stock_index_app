import { scanXlsxUrl } from "../api.js";

export default function Controls({ indices, index, onIndexChange, onRun, scan }) {
  const running = scan.state === "running";
  const pct = scan.total ? Math.round((scan.done / scan.total) * 100) : 0;

  let status = "Pick an index to start a scan.";
  let isError = false;
  if (running) status = `Scanning ${scan.done} / ${scan.total || "?"} stocks in ${scan.index}...`;
  else if (scan.state === "done") status = `Scan complete: ${scan.count} positive breakouts in ${scan.index}.`;
  else if (scan.state === "error") { status = scan.error; isError = true; }

  return (
    <section className="card controls">
      <div className="field">
        <label htmlFor="index">Market index</label>
        <select id="index" value={index} onChange={(e) => onIndexChange(e.target.value)}>
          {indices.map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </div>
      <div className="actions">
        <button className="btn primary" type="button" disabled={running || !index} onClick={onRun}>
          Run scan
        </button>
        <button className="btn" type="button"
          disabled={scan.state !== "done" || scan.rows.length === 0}
          onClick={() => { window.location.href = scanXlsxUrl(scan.jobId); }}>
          Export Excel
        </button>
      </div>
      {running && (
        <div className="progress-wrap">
          <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
            <div className="bar" style={{ width: pct + "%" }} />
          </div>
        </div>
      )}
      <p className={"status" + (isError ? " error" : "")} role="status">{status}</p>
    </section>
  );
}
