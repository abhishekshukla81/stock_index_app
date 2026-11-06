import { useCallback, useEffect, useRef, useState } from "react";
import { getScan, startScan } from "../api.js";

const POLL_MS = 2000;
const IDLE = { state: "idle", done: 0, total: 0, rows: [], count: 0, jobId: null, index: "", error: "" };

/** Starts a background scan and polls it until finished. A newer run cancels the older one. */
export default function useScan() {
  const [scan, setScan] = useState(IDLE);
  const token = useRef(0);

  useEffect(() => () => { token.current += 1; }, []);

  const run = useCallback(async (index) => {
    const mine = ++token.current;
    const alive = () => token.current === mine;
    setScan({ ...IDLE, state: "running", index });
    try {
      let data = await startScan(index);
      while (alive()) {
        if (data.state === "done") {
          setScan({ ...data, jobId: data.job_id, error: "" });
          return;
        }
        if (data.state === "error") throw new Error("Scan failed.");
        setScan({ ...IDLE, state: "running", index: data.index, done: data.done, total: data.total, jobId: data.job_id });
        await new Promise((r) => setTimeout(r, POLL_MS));
        if (!alive()) return;
        data = await getScan(data.job_id);
      }
    } catch (e) {
      if (alive()) setScan({ ...IDLE, state: "error", index, error: e.message || "Scan failed." });
    }
  }, []);

  return [scan, run];
}
