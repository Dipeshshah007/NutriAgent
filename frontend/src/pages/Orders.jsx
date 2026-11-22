import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useConfig } from "../context.jsx";

export default function Orders() {
  const [orders, setOrders] = useState(null);
  const [sp] = useSearchParams();
  const cfg = useConfig();
  const placed = sp.get("placed");
  useEffect(() => { api.get("/orders").then(setOrders); }, []);
  if (!orders) return <p className="muted">Loading…</p>;

  return (
    <>
      {placed && <div className="alert ok big">🎉 Thank you! Order #{placed} was placed successfully.</div>}
      <h2>My orders</h2>
      {orders.length === 0 && <div className="card center">No orders yet. <Link to="/catalog">Start shopping</Link></div>}
      {orders.map((o) => (
        <div className="card order" key={o.id}>
          <div className="order-head">
            <b>Order #{o.id}</b>
            <span className={`status ${o.status}`}>{o.status}</span>
            <span className="muted">{new Date(o.created_at + "Z").toLocaleString()}</span>
            <b>{cfg.currency}{o.total.toFixed(2)}</b>
          </div>
          <ul>{o.items.map((i) => <li key={i.product_id}>{i.quantity} × {i.name} — {cfg.currency}{(i.price * i.quantity).toFixed(2)}</li>)}</ul>
          <div className="muted small">Ship to: {o.full_name}, {o.address}, {o.city} {o.zip_code}</div>
        </div>
      ))}
    </>
  );
}
