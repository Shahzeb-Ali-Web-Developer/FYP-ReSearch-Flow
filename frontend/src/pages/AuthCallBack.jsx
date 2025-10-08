import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../lib/supabase";

export default function AuthCallback() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Auth callback error:", error.message);
      } else if (data.session) {
        console.log("✅ Logged in:", data.session.user);
        // Save session if you use AuthContext
        navigate("/"); // redirect where you want
      }
    };

    handleCallback();
  }, [navigate]);

  return <p>Completing sign in…</p>;
}
