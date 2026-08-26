import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@revpilot.ai");
  const [password, setPassword] = useState("secret");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const handleSubmit = async () => {
    setLoading(true); setError("");
    try { await login(email, password); navigate("/"); }
    catch { setError("Invalid credentials"); }
    finally { setLoading(false); }
  };
  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center">
      <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-green-400">RevPilot AI</h1>
          <p className="text-gray-400 mt-1 text-sm">Merchant Revenue & Growth Agent</p>
          <p className="text-xs text-yellow-500 mt-2 border border-yellow-800 rounded px-2 py-1 inline-block">DEMO · SYNTHETIC DATA · SIMULATION</p>
        </div>
        <div className="space-y-4">
          <input className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-green-500"
            placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
          <input type="password" className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-green-500"
            placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <button onClick={handleSubmit} disabled={loading}
            className="w-full bg-green-500 hover:bg-green-600 text-black font-bold py-3 rounded-lg transition">
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </div>
      </div>
    </div>
  );
}
