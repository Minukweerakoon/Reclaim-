import { useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [mode, setMode] = useState("found"); // "found" | "lost"
  const [file, setFile] = useState(null);
  const [k, setK] = useState(5);
  const [mcT, setMcT] = useState(20);
  const [debug, setDebug] = useState(false);

  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState(null);
  const [err, setErr] = useState("");

  const canSubmit = useMemo(() => !!file && !loading, [file, loading]);

  const handleSubmit = async () => {
    setErr("");
    setResp(null);
    if (!file) return;

    setLoading(true);
    try {
      const form = new FormData();
      form.append("file", file);

      let url = "";
      if (mode === "found") {
        url = `${API_BASE}/demo/found/upload?mc_T=${mcT}`;
      } else {
        url = `${API_BASE}/demo/lost/match?k=${k}&mc_T=${mcT}&debug=${debug}`;
      }

      const r = await fetch(url, {
        method: "POST",
        body: form,
      });

      const data = await r.json();
      if (!r.ok) throw new Error(data?.detail || data?.error || "Request failed");
      setResp(data);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setErr("");
    setResp(null);
    setLoading(true);
    try {
      const r = await fetch(`${API_BASE}/demo/reset`, {
        method: "POST",
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data?.detail || data?.error || "Reset failed");
      setResp(data);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const fullImageUrl = (maybePath) => {
    if (!maybePath) return "";
    if (maybePath.startsWith("http")) return maybePath;
    return `${API_BASE}${maybePath}`; // your /uploads/...
  };

  return (
    <div style={{ maxWidth: 980, margin: "40px auto", padding: 16, fontFamily: "system-ui" }}>
      <h1 style={{ marginBottom: 6 }}>Reclaim Demo — UACR Retrieval</h1>
      <p style={{ marginTop: 0, color: "#555" }}>
        Upload <b>FOUND</b> items to build the demo DB. Upload <b>LOST</b> item to find the closest match. Use <b>Reset Demo DB</b> to clear everything.
      </p>

      <div style={{ display: "flex", gap: 12, margin: "16px 0" }}>
        <button
          onClick={() => setMode("found")}
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            border: "1px solid #ddd",
            background: mode === "found" ? "#111" : "#fff",
            color: mode === "found" ? "#fff" : "#111",
            cursor: "pointer",
          }}
        >
          FOUND upload
        </button>

        <button
          onClick={() => setMode("lost")}
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            border: "1px solid #ddd",
            background: mode === "lost" ? "#111" : "#fff",
            color: mode === "lost" ? "#fff" : "#111",
            cursor: "pointer",
          }}
        >
          LOST match
        </button>
      </div>

      <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>
          {mode === "found" ? "Add FOUND item to database" : "Upload LOST item to find match"}
        </h2>

        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />

        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 14 }}>
          <label>
            <div style={{ fontSize: 12, color: "#666" }}>mc_T</div>
            <input
              type="number"
              value={mcT}
              onChange={(e) => setMcT(Number(e.target.value))}
              min={5}
              max={50}
              style={{ width: 90, padding: 8, borderRadius: 10, border: "1px solid #ddd" }}
            />
          </label>

          {mode === "lost" && (
            <>
              <label>
                <div style={{ fontSize: 12, color: "#666" }}>k</div>
                <input
                  type="number"
                  value={k}
                  onChange={(e) => setK(Number(e.target.value))}
                  min={1}
                  max={50}
                  style={{ width: 90, padding: 8, borderRadius: 10, border: "1px solid #ddd" }}
                />
              </label>

              <label style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 18 }}>
                <input type="checkbox" checked={debug} onChange={(e) => setDebug(e.target.checked)} />
                debug
              </label>
            </>
          )}
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: canSubmit ? "#2563eb" : "#eee",
              color: canSubmit ? "#fff" : "#777",
              cursor: canSubmit ? "pointer" : "not-allowed",
            }}
          >
            {loading ? "Working..." : mode === "found" ? "Upload FOUND" : "Match LOST"}
          </button>

          <button
            onClick={handleReset}
            disabled={loading}
            style={{
              padding: "10px 14px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: loading ? "#eee" : "#fff",
              color: loading ? "#777" : "#111",
              cursor: loading ? "not-allowed" : "pointer",
            }}
            title="Clears demo DB + uploaded images + in-memory FAISS index"
          >
            Reset Demo DB
          </button>
        </div>

        {err && (
          <div style={{ marginTop: 14, color: "crimson" }}>
            <b>Error:</b> {err}
          </div>
        )}
      </div>

      {resp && (
        <div style={{ marginTop: 22 }}>
          <h2>Result</h2>

          {mode === "found" ? (
            <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 16 }}>
              <div><b>Stored ID:</b> {resp.id}</div>
              <div><b>Predicted category:</b> {resp.category}</div>
              <div><b>Entropy:</b> {Number(resp.entropy).toFixed(4)}</div>
              <div><b>Alpha:</b> {Number(resp.alpha).toFixed(4)}</div>

              {resp.public_url && (
                <div style={{ marginTop: 12 }}>
                  <img
                    src={fullImageUrl(resp.public_url)}
                    alt="stored"
                    style={{ maxWidth: 320, borderRadius: 12, border: "1px solid #eee" }}
                  />
                </div>
              )}
            </div>
          ) : (
            <div style={{ border: "1px solid #eee", borderRadius: 12, padding: 16 }}>
              <div><b>Predicted category:</b> {resp.predicted_category}</div>
              <div><b>Final match category:</b> {resp.final_category}</div>
              <div><b>Final match ID:</b> {resp.final_id}</div>
              <div><b>Entropy:</b> {Number(resp.entropy).toFixed(4)}</div>
              <div><b>Alpha:</b> {Number(resp.alpha).toFixed(4)}</div>
              <div><b>Retrieval mode:</b> {resp.retrieval_mode}</div>
              <div><b>CLIP used:</b> {String(resp.clip_used)}</div>

              {resp.results?.length ? (
                <>
                  <h3 style={{ marginTop: 16 }}>Top matches</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
                    {resp.results.map((r) => (
                      <div key={r.rank} style={{ border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
                        <div><b>Rank:</b> {r.rank}</div>
                        <div><b>Category:</b> {r.category}</div>
                        <div><b>ID:</b> {r.id}</div>
                        <div><b>Final:</b> {Number(r.final_score).toFixed(4)}</div>
                        <div style={{ fontSize: 12, color: "#666" }}>
                          metric {Number(r.metric_sim).toFixed(4)} • clip {Number(r.clip_sim).toFixed(4)}
                        </div>

                        {r.image_url && (
                          <img
                            src={fullImageUrl(r.image_url)}
                            alt="match"
                            style={{ width: "100%", marginTop: 10, borderRadius: 12, border: "1px solid #eee" }}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div style={{ marginTop: 12, color: "#666" }}>No matches returned.</div>
              )}

              {resp.top_probs && (
                <>
                  <h3 style={{ marginTop: 16 }}>Top probabilities</h3>
                  <pre style={{ background: "#0b1020", color: "#cbd5e1", padding: 12, borderRadius: 12, overflowX: "auto" }}>
                    {JSON.stringify(resp.top_probs, null, 2)}
                  </pre>
                </>
              )}
            </div>
          )}

          <h3 style={{ marginTop: 16 }}>Raw JSON</h3>
          <pre style={{ background: "#0b1020", color: "#cbd5e1", padding: 12, borderRadius: 12, overflowX: "auto" }}>
            {JSON.stringify(resp, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}