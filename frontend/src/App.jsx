import { useEffect, useState } from "react";
import { getIndices } from "./api.js";
import BreakoutTable from "./components/BreakoutTable.jsx";
import Constituents from "./components/Constituents.jsx";
import Controls from "./components/Controls.jsx";
import Header from "./components/Header.jsx";
import Kpis from "./components/Kpis.jsx";
import useScan from "./hooks/useScan.js";
import useTheme from "./hooks/useTheme.js";

export default function App() {
  const [, toggleTheme] = useTheme();
  const [indices, setIndices] = useState([]);
  const [index, setIndex] = useState("");
  const [tab, setTab] = useState("scan");
  const [scan, runScan] = useScan();
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    getIndices()
      .then((list) => { setIndices(list); setIndex(list[0] || ""); })
      .catch(() => setLoadError("Could not load index list."));
  }, []);

  // Choosing an index starts its scan in the background.
  const onIndexChange = (name) => { setIndex(name); runScan(name); };

  return (
    <>
      <Header onToggleTheme={toggleTheme} />
      <main>
        <Controls indices={indices} index={index} onIndexChange={onIndexChange}
          onRun={() => runScan(index)}
          scan={loadError ? { ...scan, state: "error", error: loadError } : scan} />
        <Kpis scan={scan} />
        <section className="card results">
          <div className="tabs" role="tablist">
            {[["scan", "Breakouts"], ["const", "Constituents"]].map(([id, label]) => (
              <button key={id} type="button" role="tab" aria-selected={tab === id}
                className={"tab" + (tab === id ? " active" : "")} onClick={() => setTab(id)}>
                {label}
              </button>
            ))}
          </div>
          {tab === "scan" ? <BreakoutTable scan={scan} /> : <Constituents index={index} />}
        </section>
      </main>
      <footer className="foot">Data from Yahoo Finance and index providers. Not investment advice.</footer>
    </>
  );
}
