import { useEffect, useState } from "react";
import api from "../api/client";
import Layout from "../components/Layout";
const fmt = (n: number) => `₹${Number(n).toLocaleString("en-IN")}`;
export default function Opportunities() {
  const [opps, setOpps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const load = () => api.get("/api/v1/opportunities").then(r => setOpps(r.data)).finally(() => setLoading(false));
  const detect = async () => {
    setDetecting(true);
    await api.post("/api/v1/opportunities/detect");
    await load();
    setDetecting(false);
  };
  useEffect(() => { load(); }, []);
  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <div><h2 className="text-2xl font-bold text-white">Opportunities</h2>
          <p className="text-gray-400 text-sm mt-1">Evidence-backed revenue opportunities</p></div>
        <button onClick={detect} disabled={detecting}
          className="bg-green-500 hover:bg-green-600 text-black font-bold px-4 py-2 rounded-lg transition text-sm">
          {detecting ? "Detecting..." : "Run Detection"}
        </button>
      </div>
      {loading ? <p className="text-gray-400">Loading...</p> : (
        <div className="space-y-3">
          {opps.map((o: any) => (
            <div key={o.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded mr-2 ${o.priority === "high" ? "bg-red-500/20 text-red-400" : o.priority === "medium" ? "bg-yellow-500/20 text-yellow-400" : "bg-gray-700 text-gray-400"}`}>
                    {o.priority?.toUpperCase()}
                  </span>
                  <span className="text-white font-medium">{o.title}</span>
                </div>
                <span className="text-green-400 font-bold">{fmt(o.estimated_revenue_impact || 0)}</span>
              </div>
              <p className="text-gray-400 text-sm mt-2">{o.description}</p>
              <p className="text-xs text-gray-500 mt-2">Confidence: {o.confidence} · Type: {o.type?.replace(/_/g, " ")}</p>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
