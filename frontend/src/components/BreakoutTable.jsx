import { useMemo, useState } from "react";

const COLS = [
  { key: "Date", label: "Scan date", type: "text" },
  { key: "Ticker", label: "Ticker", type: "text", cls: "ticker" },
  { key: "Stock", label: "Stock", type: "text", cls: "muted-cell" },
  { key: "CMP", label: "CMP", type: "num", cls: "strong" },
  { key: "52W High", label: "52W High", type: "num" },
  { key: "52W High Date", label: "52W High Date", type: "date" },
  { key: "30 DMA", label: "30 DMA", type: "num" },
  { key: "50 DMA", label: "50 DMA", type: "num" },
  { key: "200 DMA", label: "200 DMA", type: "num" },
  { key: "200 DMA Dist %", label: "200 DMA Dist %", type: "pct" },
  { key: "CAR Status", label: "CAR", type: "badge" },
  { key: "Action", label: "Action", type: "badge" },
];

const fmt = new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const isNum = (c) => c.type === "num" || c.type === "pct";

// dd-mm-yyyy -> sortable number
function dateVal(s) {
  const [d, m, y] = String(s).split("-").map(Number);
  return y * 10000 + m * 100 + d;
}

function sortVal(row, col) {
  const v = row[col.key];
  if (col.type === "date") return dateVal(v);
  if (isNum(col)) return Number(v);
  return String(v).toLowerCase();
}

function Cell({ row, col }) {
  const v = row[col.key];
  const cls = [isNum(col) ? "num" : "", col.cls || ""].join(" ").trim();
  let content = String(v);
  if (col.type === "num") content = fmt.format(v);
  else if (col.type === "pct") content = <span className="pill">{fmt.format(v)}%</span>;
  else if (col.type === "badge") content = <span className="badge">{String(v)}</span>;
  return <td className={cls}>{content}</td>;
}

export default function BreakoutTable({ scan }) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("200 DMA Dist %");
  const [desc, setDesc] = useState(false);
  const rows = scan.rows;

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const col = COLS.find((c) => c.key === sortKey);
    return rows
      .filter((r) => !q || r.Ticker.toLowerCase().includes(q) || r.Stock.toLowerCase().includes(q))
      .sort((a, b) => {
        const x = sortVal(a, col), y = sortVal(b, col);
        const c = x < y ? -1 : x > y ? 1 : 0;
        return desc ? -c : c;
      });
  }, [rows, query, sortKey, desc]);

  const onSort = (col) => {
    if (sortKey === col.key) setDesc((d) => !d);
    else { setSortKey(col.key); setDesc(col.type !== "text"); }
  };

  return (
    <div>
      <div className="toolbar">
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by ticker or name" aria-label="Filter results" autoComplete="off" />
        <span className="muted">{rows.length ? `${shown.length} of ${rows.length} shown` : ""}</span>
      </div>

      {shown.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {COLS.map((c) => {
                  const on = c.key === sortKey;
                  const cls = ["sortable", isNum(c) ? "num" : "", on ? "sorted" : "", on && desc ? "desc" : ""]
                    .join(" ").replace(/\s+/g, " ").trim();
                  return <th key={c.key} className={cls} onClick={() => onSort(c)}>{c.label}</th>;
                })}
              </tr>
            </thead>
            <tbody>
              {shown.map((r) => (
                <tr key={r.Ticker}>{COLS.map((c) => <Cell key={c.key} row={r} col={c} />)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {scan.state === "done" && rows.length === 0 && (
        <div className="empty">
          <div className="empty-icon" aria-hidden="true" />
          <p>No stocks met all breakout conditions.</p>
        </div>
      )}

      <p className="note">
        A stock qualifies when its close is above the 30, 50 and 200 day moving averages and the
        cumulative average (CAR) of closes since the 52-week closing high has risen for the last 10 sessions.
      </p>
    </div>
  );
}
