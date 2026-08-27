import { useEffect, useState } from "react";
import api from "../api/client";
import StatCard from "../components/StatCard";
import Layout from "../components/Layout";
const fmt = (n: number) => `₹${Number(n).toLocaleString("en-IN")}`;
const pct = (n: number) => `${(Number(n) * 100).toFixed(1)}%`;
export default function Overview() {
  const [data, setData] = useState<any>(null);
  const [opps, setOpps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api.get("/api/v1/analytics/overview"), api.get("/api/v1/opportunities/")])
      .then(([ov, op]) => { setData(ov.data); setOpps(op.data.slice(0, 3)); })
      .catch(() => setError("Failed to load data"))
      .finally(() => setLoading(false));
  }, []);
  if (loading) return <Layout><div className="text-gray-400 mt-20 text-center">Loading...</div></Layout>;
  if (error) return <Layout><div className="text-red-400 mt-20 text-center">{error}</div></Layout>;
  const r = data?.revenue || {}; const p = data?.payments || {};
  const c = data?.checkout || {}; const cu = data?.customers || {};
  return (
    <Layout>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white">Overview</h2>
        <p className="text-gray-400 text-sm mt-1">Revenue intelligence summary</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Gross Revenue" value={fmt(r.gross_revenue || 0)} color="text-green-400" />
        <StatCard label="Net Revenue" value={fmt(r.net_revenue || 0)} />
        <StatCard label="Payment Success" value={pct(p.success_rate || 0)} color="text-blue-400" />
        <StatCard label="Failed Payment Value" value={fmt(p.failed_payment_value || 0)} color="text-red-400" />
        <StatCard label="Checkout Abandonment" value={pct(c.abandonment_rate || 0)} color="text-yellow-400" />
        <StatCard label="Abandoned Value" value={fmt(c.abandoned_value || 0)} color="text-orange-400" />
        <StatCard label="Active Customers" value={cu.active_customers || 0} />
        <StatCard label="Total Orders" value={r.order_count || 0} />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Top Revenue Opportunities</h3>
        {opps.length === 0 && <p className="text-gray-500">No opportunities detected.</p>}
        <div className="space-y-3">
          {opps.map((o: any) => (
            <div key={o.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start justify-between">
                <div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded mr-2 ${o.priority === "high" ? "bg-red-500/20 text-red-400" : o.priority === "medium" ? "bg-yellow-500/20 text-yellow-400" : "bg-gray-700 text-gray-400"}`}>
                    {o.priority?.toUpperCase()}
                  </span>
                  <span className="text-white font-medium">{o.title}</span>
                </div>
                <span className="text-green-400 font-bold text-sm">{fmt(o.estimated_revenue_impact || 0)}</span>
              </div>
              <p className="text-gray-400 text-sm mt-2">{o.description}</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
