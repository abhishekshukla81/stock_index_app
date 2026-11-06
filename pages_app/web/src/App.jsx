import { useEffect, useState } from "react";
import { getManifest } from "./api.js";
import BreakoutTable from "./components/BreakoutTable.jsx";
import Controls from "./components/Controls.jsx";
import Header from "./components/Header.jsx";
import Kpis from "./components/Kpis.jsx";
import useIndexData from "./hooks/useIndexData.js";
import useTheme from "./hooks/useTheme.js";

export default function App() {
  const [, toggleTheme] = useTheme();
  const [indices, setIndices] = useState([]);
  const [selected, setSelected] = useState("");
  const [manifestError, setManifestError] = useState("");

  useEffect(() => {
    getManifest()
      .then((m) => { setIndices(m.indices); setSelected(m.indices[0]?.name || ""); })
      .catch((e) => setManifestError(e.message));
  }, []);

  const entry = indices.find((i) => i.name === selected);
  const state = useIndexData(entry?.file);
  const shown = manifestError ? { status: "error", data: null, error: manifestError } : state;

  return (
    <>
      <Header onToggleTheme={toggleTheme} />
      <main>
        <Controls indices={indices} selected={selected} onSelect={setSelected} state={shown} />
        <Kpis scan={shown.status === "done" ? shown.data : null} />
        <section className="card results">
          {shown.status === "done" && <BreakoutTable scan={shown.data} />}
        </section>
      </main>
      <footer className="foot">Daily snapshot from Yahoo Finance and index providers. Not investment advice.</footer>
    </>
  );
}
