import { useEffect, useState } from "react";
import api from "../api/client";
import Layout from "../components/Layout";
import StatCard from "../components/StatCard";
const fmt = (n: any) => typeof n === "number" ? (n > 999 ? `₹${Number(n).toLocaleString("en-IN")}` : String(Number(n).toFixed(2))) : String(n ?? "-");
export default function Subscriptions() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api.get("/api/v1/analytics/subscriptions")
      .then(r => setData(r.data))
      .catch(() => setError("Failed to load"))
      .finally(() => setLoading(false));
  }, []);
  if (loading) return <Layout><p className="text-gray-400 mt-20 text-center">Loading...</p></Layout>;
  if (error) return <Layout><p className="text-red-400 mt-20 text-center">{error}</p></Layout>;
  return (
    <Layout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Subscriptions</h2>
        <p className="text-gray-400 text-sm mt-1">Analytics · Synthetic Data</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {data && Object.entries(data).filter(([,v]) => typeof v !== "object").map(([k, v]) => (
          <StatCard key={k} label={k.replace(/_/g," ")} value={fmt(v as any)} />
        ))}
      </div>
    </Layout>
  );
}
