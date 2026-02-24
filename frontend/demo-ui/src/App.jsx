import { useState } from "react";
import { supabase } from "./supabaseClient";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ReclaimPage } from "./pages/ReclaimPage";

/*
  CORE PIPELINE LOGIC (UNCHANGED BACKEND BEHAVIOR)

  This function will be reused by the new Magic Pattern UI.
  We are separating logic from UI so the backend integration
  stays clean and reusable.
*/

export async function processItem({
  status,
  file,
  userCategory = null,
  userId = "demo_user",
  userEmail = "demo@test.com",
}) {
  if (!file) throw new Error("Image file is required");

  const fileExt = file.name.split(".").pop();
  const tempId = crypto.randomUUID();
  const filePath = `${status}/${tempId}.${fileExt}`;

  // 1️⃣ Upload image to Supabase Storage
  const { error: uploadError } = await supabase.storage
    .from("items")
    .upload(filePath, file);

  if (uploadError) throw uploadError;

  // 2️⃣ Get public URL
  const { data } = supabase.storage.from("items").getPublicUrl(filePath);
  const imageUrl = data.publicUrl;

  // 3️⃣ Insert row into unified "items" table
  const { data: inserted, error: insertError } = await supabase
    .from("items")
    .insert({
      user_id: userId,
      user_email: userEmail,
      item_type: status,
      image_url: imageUrl,
      user_category: userCategory,
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
    k: 4,
    mc_T: 20,
  };

  const res = await fetch("http://127.0.0.1:8000/items/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const responseData = await res.json();
  return responseData;
}

/*
  TEMPORARY ROOT COMPONENT

  We will replace this UI with the Magic Pattern layout.
  Backend logic now lives in processItem().
*/

function App() {
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("home");

  const handleNavigate = (page) => {
    if (page === "chat" && !user) {
      setCurrentPage("login");
      return;
    }
    setCurrentPage(page);
  };

  if (currentPage === "login") {
    return (
      <LoginPage
        onLogin={(u) => {
          setUser(u);
          setCurrentPage("chat");
        }}
        onBack={() => setCurrentPage("home")}
      />
    );
  }

  return (
    <>
      {currentPage === "home" ? (
        <HomePage
          onNavigate={handleNavigate}
          user={user}
          onSignOut={() => {
            setUser(null);
            setCurrentPage("home");
          }}
        />
      ) : (
        <ReclaimPage
          onNavigate={handleNavigate}
          user={user}
          onSignOut={() => {
            setUser(null);
            setCurrentPage("home");
          }}
        />
      )}
    </>
  );
}

export default App;
