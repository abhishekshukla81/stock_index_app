import { useEffect, useState } from "react";
import { constituentsCsvUrl, getConstituents } from "../api.js";

export default function Constituents({ index }) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("Loading...");

  useEffect(() => {
    if (!index) return undefined;
    let live = true;
    setData(null);
    setStatus("Loading...");
    getConstituents(index)
      .then((d) => { if (live) { setData(d); setStatus(`${d.count} constituents in ${d.index}`); } })
      .catch((e) => { if (live) setStatus(e.message); });
    return () => { live = false; };
  }, [index]);

  return (
    <div>
      <div className="toolbar">
        <span className="muted" role="status">{status}</span>
        <button className="btn" type="button" disabled={!data}
          onClick={() => { window.location.href = constituentsCsvUrl(index); }}>
          Export CSV
        </button>
      </div>
      {data && (
        <div className="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Ticker</th></tr></thead>
            <tbody>
              {data.tickers.map((t, i) => (
                <tr key={t}><td className="muted-cell">{i + 1}</td><td className="ticker">{t}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
