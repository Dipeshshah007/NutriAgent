import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import { useAuth } from "./context.jsx";
import Home from "./pages/Home.jsx";
import Catalog from "./pages/Catalog.jsx";
import ProductDetail from "./pages/ProductDetail.jsx";
import Cart from "./pages/Cart.jsx";
import Checkout from "./pages/Checkout.jsx";
import Orders from "./pages/Orders.jsx";
import Profile from "./pages/Profile.jsx";
import Planner from "./pages/Planner.jsx";
import Tracker from "./pages/Tracker.jsx";
import Coach from "./pages/Coach.jsx";
import { Login, Register, AdminLogin } from "./pages/Auth.jsx";
import Admin from "./pages/Admin.jsx";

function Protected({ children, admin = false }) {
  const { user } = useAuth();
  const loc = useLocation();
  if (!user) return <Navigate to={admin ? "/admin/login" : "/login"} state={{ from: loc.pathname }} replace />;
  if (admin && user.role !== "admin") return <Navigate to="/admin/login" replace />;
  if (!admin && user.role === "admin") return <Navigate to="/admin" replace />;
  return children;
}

export default function App() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/catalog" element={<Catalog />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/cart" element={<Protected><Cart /></Protected>} />
          <Route path="/checkout" element={<Protected><Checkout /></Protected>} />
          <Route path="/orders" element={<Protected><Orders /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="/planner" element={<Protected><Planner /></Protected>} />
          <Route path="/tracker" element={<Protected><Tracker /></Protected>} />
          <Route path="/coach" element={<Protected><Coach /></Protected>} />
          <Route path="/admin" element={<Protected admin><Admin /></Protected>} />
          <Route path="*" element={<div className="card center"><h2>Page not found</h2></div>} />
        </Routes>
      </main>
      <footer className="footer">Wellness guidance only — not medical advice. Demo project; no real payments are processed.</footer>
    </>
  );
}
