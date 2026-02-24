import { useState } from "react";
import { supabase } from "./supabaseClient";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ReclaimPage } from "./pages/ReclaimPage";

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
