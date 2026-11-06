import { xlsxUrl } from "../api.js";

function ago(iso) {
  const mins = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (mins < 60) return `${mins} min ago`;
  if (mins < 2880) return `${Math.round(mins / 60)} h ago`;
  return `${Math.round(mins / 1440)} days ago`;
}

export default function Controls({ indices, selected, onSelect, state }) {
  const entry = indices.find((i) => i.name === selected);
  const { status, data, error } = state;

  let text = "Loading...";
  let isError = false;
  if (status === "error") { text = error; isError = true; }
  else if (status === "done") {
    const when = new Date(data.generated_at);
    text = `${data.count} positive breakouts of ${data.total} stocks. Last scan ${when.toLocaleString()} (${ago(data.generated_at)}).`;
  }

  return (
    <section className="card controls">
      <div className="field">
        <label htmlFor="index">Market index</label>
        <select id="index" value={selected} onChange={(e) => onSelect(e.target.value)}>
          {indices.map((i) => <option key={i.name} value={i.name}>{i.name}</option>)}
        </select>
      </div>
      <div className="actions">
        <a className={"btn" + (status === "done" && data.count ? "" : " disabled")}
          href={status === "done" && data.count ? xlsxUrl(entry.xlsx) : undefined}
          download aria-disabled={!(status === "done" && data.count)}>
          Export Excel
        </a>
      </div>
      <p className={"status" + (isError ? " error" : "")} role="status">{text}</p>
      {status === "done" && data.stale && (
        <p className="status error">
          The latest refresh failed for this index; showing the previous result from the date above.
        </p>
      )}
    </section>
  );
}
