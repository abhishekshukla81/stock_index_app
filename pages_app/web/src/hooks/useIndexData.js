import { useEffect, useState } from "react";
import { getIndexData } from "../api.js";

/** Loads the pre-computed scan for one index file. */
export default function useIndexData(file) {
  const [state, setState] = useState({ status: "idle", data: null, error: "" });

  useEffect(() => {
    if (!file) return undefined;
    let live = true;
    setState({ status: "loading", data: null, error: "" });
    getIndexData(file)
      .then((data) => { if (live) setState({ status: "done", data, error: "" }); })
      .catch((e) => { if (live) setState({ status: "error", data: null, error: e.message }); });
    return () => { live = false; };
  }, [file]);

  return state;
}
