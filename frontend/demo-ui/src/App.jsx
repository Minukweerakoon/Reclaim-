import { useEffect, useState } from "react";
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

  useEffect(() => {
    // Get existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listen for auth changes
    const { data: listener } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setUser(session?.user ?? null);
      }
    );

    return () => {
      listener.subscription.unsubscribe();
    };
  }, []);

  const handleNavigate = (page) => {
    if (page === "chat" && !user) {
      setCurrentPage("login");
      return;
    }
    setCurrentPage(page);
  };

  if (currentPage === "login") {
    return <LoginPage onBack={() => setCurrentPage("home")} />;
  }

  return (
    <>
      {currentPage === "home" ? (
        <HomePage
          onNavigate={handleNavigate}
          user={user}
          onSignOut={async () => {
            await supabase.auth.signOut();
            setUser(null);
            setCurrentPage("home");
          }}
        />
      ) : (
        <ReclaimPage
          onNavigate={handleNavigate}
          user={user}
          onSignOut={async () => {
            await supabase.auth.signOut();
            setUser(null);
            setCurrentPage("home");
          }}
        />
      )}
    </>
  );
}

export default App;
