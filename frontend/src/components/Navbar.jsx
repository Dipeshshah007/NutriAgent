import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth, useCart, useConfig } from "../context.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const cart = useCart();
  const cfg = useConfig();
  const nav = useNavigate();
  const isAdmin = user?.role === "admin";

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand">🥗 {cfg.app_name}</Link>
        <nav className="links">
          <NavLink to="/catalog">Shop</NavLink>
          {user && !isAdmin && (
            <>
              <NavLink to="/planner">Meal Planner</NavLink>
              <NavLink to="/tracker">Tracker</NavLink>
              <NavLink to="/coach">AI Coach</NavLink>
              <NavLink to="/orders">Orders</NavLink>
            </>
          )}
          {isAdmin && <NavLink to="/admin">Admin Panel</NavLink>}
        </nav>
        <div className="nav-right">
          {user && !isAdmin && (
            <Link to="/cart" className="cart-btn">🛒 Cart{cart.count > 0 && <span className="badge">{cart.count}</span>}</Link>
          )}
          {user ? (
            <>
              {!isAdmin && <Link to="/profile" className="muted-link">👤 {user.name.split(" ")[0]}</Link>}
              <button className="btn ghost sm" onClick={() => { logout(); nav("/"); }}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn ghost sm">Login</Link>
              <Link to="/register" className="btn sm">Sign up</Link>
              <Link to="/admin/login" className="muted-link small">Admin</Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
