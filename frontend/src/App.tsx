import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Payments from "./pages/Payments";
import Revenue from "./pages/Revenue";
import Checkout from "./pages/Checkout";
import Customers from "./pages/Customers";
import Subscriptions from "./pages/Subscriptions";
import Opportunities from "./pages/Opportunities";
import Strategy from "./pages/Strategy";

function Protected({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<Protected><Overview /></Protected>} />
          <Route path="/revenue" element={<Protected><Revenue /></Protected>} />
          <Route path="/payments" element={<Protected><Payments /></Protected>} />
          <Route path="/checkout" element={<Protected><Checkout /></Protected>} />
          <Route path="/customers" element={<Protected><Customers /></Protected>} />
          <Route path="/subscriptions" element={<Protected><Subscriptions /></Protected>} />
          <Route path="/opportunities" element={<Protected><Opportunities /></Protected>} />
          <Route path="/strategy" element={<Protected><Strategy /></Protected>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
