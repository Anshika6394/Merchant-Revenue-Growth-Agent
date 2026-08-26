import { type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
const nav = [
  { path: "/", label: "Overview" },
  { path: "/revenue", label: "Revenue" },
  { path: "/payments", label: "Payments" },
  { path: "/checkout", label: "Checkout" },
  { path: "/customers", label: "Customers" },
  { path: "/subscriptions", label: "Subscriptions" },
  { path: "/opportunities", label: "Opportunities" },
  { path: "/strategy", label: "AI Strategy" },
];
export default function Layout({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  const { logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gray-950 flex">
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-5 border-b border-gray-800">
          <h1 className="text-xl font-bold text-green-400">RevPilot AI</h1>
          <p className="text-xs text-gray-500 mt-1">Revenue Growth Agent</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {nav.map(({ path, label }) => (
            <Link key={path} to={path}
              className={`block px-3 py-2 rounded-lg text-sm transition ${pathname === path ? "bg-green-500/10 text-green-400 font-medium" : "text-gray-400 hover:text-white hover:bg-gray-800"}`}>
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <p className="text-xs text-yellow-600 mb-2 px-3">SYNTHETIC DATA</p>
          <button onClick={() => { logout(); navigate("/login"); }}
            className="w-full text-left px-3 py-2 text-sm text-gray-500 hover:text-white rounded-lg hover:bg-gray-800 transition">
            Sign Out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
