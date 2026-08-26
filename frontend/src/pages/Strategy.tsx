import { useState } from "react";
import api from "../api/client";
import Layout from "../components/Layout";
const fmt = (n: number) => `₹${Number(n).toLocaleString("en-IN")}`;
const SUGGESTIONS = [
  "What should I focus on today?",
  "Where am I losing revenue?",
  "How can I increase revenue?",
  "What payment problem should I fix first?",
];
export default function Strategy() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const run = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try { const res = await api.post("/api/v1/agent/strategy", { query: q }); setResult(res.data); }
    catch { setError("Strategy agent unavailable. Try again."); }
    finally { setLoading(false); }
  };
  return (
    <Layout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">AI Strategy</h2>
        <p className="text-gray-400 text-sm mt-1">Ask RevPilot AI what to prioritize</p>
      </div>
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
        <div className="flex gap-3">
          <input className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-green-500"
            placeholder="Ask a revenue question..." value={query} onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && run(query)} />
          <button onClick={() => run(query)} disabled={loading}
            className="bg-green-500 hover:bg-green-600 text-black font-bold px-5 rounded-lg transition">
            {loading ? "..." : "Ask"}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => { setQuery(s); run(s); }}
              className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded-full transition">{s}</button>
          ))}
        </div>
      </div>
      {error && <div className="bg-red-500/10 border border-red-800 rounded-xl p-4 text-red-400 mb-4">{error}</div>}
      {result && (
        <div className="space-y-4">
          <div className="bg-gray-900 border border-green-800 rounded-xl p-5">
            <h3 className="text-green-400 font-semibold mb-2">Executive Summary</h3>
            <p className="text-white">{result.executive_summary}</p>
            <p className="text-gray-400 text-sm mt-2">Total estimated impact: <span className="text-green-400 font-bold">{fmt(result.total_estimated_impact || 0)}</span></p>
          </div>
          {(result.top_opportunities || []).map((o: any, i: number) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex justify-between items-start mb-2">
                <span className="text-white font-medium">#{i+1} {o.opportunity_type?.replace(/_/g," ")}</span>
                <span className="text-green-400 font-bold">{fmt(o.estimated_impact?.value || 0)}</span>
              </div>
              <p className="text-gray-300 text-sm mb-2">{o.summary}</p>
              <p className="text-gray-400 text-sm"><span className="text-gray-500">Action: </span>{o.recommended_action}</p>
              <div className="flex gap-3 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded ${o.priority==="high"?"bg-red-500/20 text-red-400":"bg-yellow-500/20 text-yellow-400"}`}>{o.priority}</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">{o.confidence} confidence</span>
              </div>
            </div>
          ))}
          {result.recommended_next_steps?.length > 0 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-3">Recommended Next Steps</h3>
              <ol className="space-y-2">
                {result.recommended_next_steps.map((s: string, i: number) => (
                  <li key={i} className="text-gray-300 text-sm flex gap-2"><span className="text-green-400 font-bold">{i+1}.</span>{s}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </Layout>
  );
}
