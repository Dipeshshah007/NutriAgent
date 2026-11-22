import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "./api";

const AuthCtx = createContext(null);
const CartCtx = createContext(null);
const ToastCtx = createContext(() => {});
const ConfigCtx = createContext({ app_name: "NutriAgent", currency: "$" });

export const useAuth = () => useContext(AuthCtx);
export const useCart = () => useContext(CartCtx);
export const useToast = () => useContext(ToastCtx);
export const useConfig = () => useContext(ConfigCtx);

export function Providers({ children }) {
  const [config, setConfig] = useState({ app_name: "NutriAgent", tagline: "", currency: "$" });
  const [user, setUser] = useState(() => JSON.parse(localStorage.getItem("user") || "null"));
  const [cart, setCart] = useState({ items: [], count: 0, subtotal: 0, tax: 0, shipping: 0, total: 0, warnings: [], nutrition: {} });
  const [toast, setToast] = useState(null);

  const notify = useCallback((msg, type = "ok") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 2800);
  }, []);

  useEffect(() => {
    api.get("/config").then((c) => { setConfig(c); document.title = c.app_name; }).catch(() => {});
  }, []);

  const saveSession = (data) => {
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  };
  const logout = useCallback(() => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setUser(null);
    setCart((c) => ({ ...c, items: [], count: 0 }));
  }, []);

  const auth = {
    user,
    login: async (email, password, admin = false) =>
      saveSession(await api.post(admin ? "/auth/admin-login" : "/auth/login", { email, password })),
    register: async (name, email, password) => saveSession(await api.post("/auth/register", { name, email, password })),
    logout,
  };

  const refreshCart = useCallback(async () => {
    if (!localStorage.getItem("token")) return;
    try { setCart(await api.get("/cart")); } catch (e) { if (e.status === 401) logout(); }
  }, [logout]);

  useEffect(() => { if (user && user.role !== "admin") refreshCart(); }, [user, refreshCart]);

  const run = async (fn, okMsg) => {
    try { setCart(await fn()); if (okMsg) notify(okMsg); } catch (e) { notify(e.message, "err"); }
  };
  const cartApi = {
    ...cart,
    refresh: refreshCart,
    add: (product_id, quantity = 1) => run(() => api.post("/cart", { product_id, quantity }), "Added to cart"),
    setQty: (id, quantity) => run(() => api.put(`/cart/${id}`, { quantity })),
    remove: (id) => run(() => api.del(`/cart/${id}`), "Removed"),
  };

  return (
    <ConfigCtx.Provider value={config}>
      <ToastCtx.Provider value={notify}>
        <AuthCtx.Provider value={auth}>
          <CartCtx.Provider value={cartApi}>
            {children}
            {toast && <div className={`toast ${toast.type}`}>{toast.msg}</div>}
          </CartCtx.Provider>
        </AuthCtx.Provider>
      </ToastCtx.Provider>
    </ConfigCtx.Provider>
  );
}
