// Relative URLs so the app also works behind the Colab proxy.
async function request(url, options) {
  const res = await fetch(url, options);
  let data = {};
  try {
    data = await res.json();
  } catch {
    // non-JSON error body
  }
  if (!res.ok) throw new Error(data.error || "Request failed.");
  return data;
}

export const getIndices = () => request("api/indices").then((d) => d.indices);
export const getConstituents = (index) =>
  request("api/constituents?index=" + encodeURIComponent(index));
export const startScan = (index) =>
  request("api/scan?index=" + encodeURIComponent(index), { method: "POST" });
export const getScan = (jobId) => request("api/scan/" + encodeURIComponent(jobId));

export const constituentsCsvUrl = (index) => "api/export?index=" + encodeURIComponent(index);
export const scanXlsxUrl = (jobId) => "api/scan/" + encodeURIComponent(jobId) + "/export";
