import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth, useCart, useToast } from "../context.jsx";
import { Summary } from "./Cart.jsx";

export default function Checkout() {
  const cart = useCart();
  const { user } = useAuth();
  const notify = useToast();
  const nav = useNavigate();
  const [f, setF] = useState({ full_name: user?.name || "", address: "", city: "", zip_code: "", payment_method: "card", card_number: "4242 4242 4242 4242" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  if (cart.items.length === 0)
    return <div className="card center"><h2>Nothing to check out</h2><Link className="btn" to="/catalog">Browse the shop</Link></div>;

  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try {
      const order = await api.post("/orders", f);
      await cart.refresh();
      notify(`Order #${order.id} placed!`);
      nav(`/orders?placed=${order.id}`);
    } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };

  return (
    <form className="layout cart-layout" onSubmit={submit}>
      <section className="card">
        <h2>Checkout</h2>
        <h3>Delivery address</h3>
        <label>Full name<input required value={f.full_name} onChange={set("full_name")} /></label>
        <label>Street address<input required value={f.address} onChange={set("address")} /></label>
        <div className="two">
          <label>City<input required value={f.city} onChange={set("city")} /></label>
          <label>ZIP / Postal code<input required value={f.zip_code} onChange={set("zip_code")} /></label>
        </div>
        <h3>Payment</h3>
        <div className="radios">
          {[["card", "Credit / debit card"], ["upi", "UPI"], ["cod", "Cash on delivery"]].map(([v, l]) => (
            <label key={v} className="radio"><input type="radio" name="pm" checked={f.payment_method === v} onChange={() => setF({ ...f, payment_method: v })} /> {l}</label>
          ))}
        </div>
        {f.payment_method === "card" && (
          <label>Card number (demo — use 4242 4242 4242 4242)<input value={f.card_number} onChange={set("card_number")} /></label>
        )}
        <div className="hint">🔒 Demo store: no real payment is processed and card numbers are never stored.</div>
        {err && <div className="alert err">{err}</div>}
      </section>
      <aside className="card">
        <h3>Your order</h3>
        {cart.items.map((i) => <div key={i.product_id} className="line"><span>{i.quantity} × {i.name}</span><span>{i.line_total.toFixed(2)}</span></div>)}
        <Summary cart={cart} />
        <button className="btn block" disabled={busy}>{busy ? "Placing order…" : `Place order`}</button>
      </aside>
    </form>
  );
}
