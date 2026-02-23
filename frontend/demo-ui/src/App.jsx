import { useState } from "react";
import "./App.css";
import { supabase } from "./supabaseClient";

function App() {
  const [status, setStatus] = useState("lost");
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!file) return alert("Please select an image");

    setLoading(true);
    setResults(null);

    try {
      const fileExt = file.name.split(".").pop();
      const tempId = crypto.randomUUID();
      const filePath = `${status}/${tempId}.${fileExt}`;

      // 1️⃣ Upload image to Supabase Storage
      const { error: uploadError } = await supabase.storage
        .from("items")
        .upload(filePath, file);

      if (uploadError) throw uploadError;

      // 2️⃣ Get public URL
      const { data } = supabase.storage
        .from("items")
        .getPublicUrl(filePath);

      const imageUrl = data.publicUrl;

      // 3️⃣ Insert row into unified "items" table
      const { data: inserted, error: insertError } = await supabase
        .from("items")
        .insert({
          user_id: "demo_user",
          user_email: "demo@test.com",
          item_type: status,
          image_url: imageUrl,
          user_category: null,
          status: "active",
        })
        .select();

      if (insertError) throw insertError;

      const itemId = inserted[0].id;

      // 4️⃣ Call AI backend
      const payload = {
        item_id: itemId,
        item_type: status,
        image_url: imageUrl,
        k: 5,
        mc_T: 20,
      };

      const res = await fetch("http://127.0.0.1:8000/items/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const responseData = await res.json();
      setResults(responseData);
    } catch (err) {
      console.error(err);
      alert("Error processing item");
    }

    setLoading(false);
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial" }}>
      <h2>Reclaim AI — Storage + AI Pipeline</h2>

      <div style={{ marginBottom: "20px" }}>
        <label>Status: </label>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="lost">Lost</option>
          <option value="found">Found</option>
        </select>
      </div>

      <div style={{ marginBottom: "20px" }}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files[0])}
        />
      </div>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? "Processing..." : "Submit"}
      </button>

      <hr style={{ margin: "40px 0" }} />

      {results && results.status === "indexed" && (
        <div>
          <h3>Item Indexed Successfully</h3>
          <p>Category: {results.category}</p>
          <p>Entropy: {results.entropy}</p>
          <p>Alpha: {results.alpha}</p>
        </div>
      )}

      {results && results.results && (
        <div>
          <h3>Retrieval Results</h3>
          {results.results.map((r) => (
            <div
              key={r.id}
              style={{
                border: "1px solid #ccc",
                padding: "10px",
                marginBottom: "15px",
              }}
            >
              <p><strong>Rank:</strong> {r.rank}</p>
              <p><strong>Category:</strong> {r.category}</p>
              <p><strong>Score:</strong> {r.score.toFixed(4)}</p>
              <img
                src={r.image_url}
                alt="result"
                style={{ maxWidth: "200px" }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
