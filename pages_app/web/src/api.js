// Static data produced by pages_app/generate.py. Relative URLs so the app works
// under a GitHub Pages sub-path (https://<user>.github.io/<repo>/).
async function getJson(path) {
  const res = await fetch(path, { cache: "no-cache" });
  if (!res.ok) throw new Error("Data not available yet.");
  return res.json();
}

export const getManifest = () => getJson("data/manifest.json");
export const getIndexData = (file) => getJson("data/" + encodeURIComponent(file));
export const xlsxUrl = (file) => "data/" + encodeURIComponent(file);
