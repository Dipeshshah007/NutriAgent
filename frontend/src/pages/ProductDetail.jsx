import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, emojiFor } from "../api";
import { useAuth, useCart, useConfig } from "../context.jsx";

export default function ProductDetail() {
  const { id } = useParams();
  const [p, setP] = useState(null);
  const [qty, setQty] = useState(1);
  const [err, setErr] = useState("");
  const { user } = useAuth();
  const cart = useCart();
  const cfg = useConfig();
  const nav = useNavigate();

  useEffect(() => { api.get(`/products/${id}`).then(setP).catch((e) => setErr(e.message)); }, [id]);
  if (err) return <div className="card center">{err}</div>;
  if (!p) return <p className="muted">Loading…</p>;

  const total = p.protein * 4 + p.carbs * 4 + p.fat * 9 || 1;
  const bars = [["Protein", p.protein * 4 / total, "#16a34a"], ["Carbs", p.carbs * 4 / total, "#f59e0b"], ["Fat", p.fat * 9 / total, "#ef4444"]];

  return (
    <div className="card detail">
      <div className="big-thumb">{p.image_url ? <img src={p.image_url} alt="" /> : emojiFor(p.category)}</div>
      <div>
        <div className="tags">{p.tags.map((t) => <span key={t} className="tag">{t}</span>)}</div>
        <h1>{p.name}</h1>
        <p className="muted">{p.description}</p>
        <div className="price big">{cfg.currency}{p.price.toFixed(2)} <small className="muted">/ {p.serving}</small></div>

        <h3>Nutrition per serving</h3>
        <table className="nutri"><tbody>
          <tr><td>Calories</td><td>{p.calories} kcal</td></tr>
          <tr><td>Protein</td><td>{p.protein} g</td></tr>
          <tr><td>Carbohydrates</td><td>{p.carbs} g</td></tr>
          <tr><td>Fat</td><td>{p.fat} g</td></tr>
          <tr><td>Fibre</td><td>{p.fiber} g</td></tr>
        </tbody></table>
        <div className="splitbar">{bars.map(([n, v, c]) => <div key={n} style={{ width: `${v * 100}%`, background: c }} title={`${n} ${Math.round(v * 100)}% of calories`} />)}</div>
        <div className="legend">{bars.map(([n, v, c]) => <span key={n}><i style={{ background: c }} />{n} {Math.round(v * 100)}%</span>)}</div>

        {p.allergens.length > 0 && <div className="alert warn">⚠ Contains: {p.allergens.join(", ")}</div>}
        <div className="qty-row">
          <input type="number" min="1" max={Math.max(1, p.stock)} value={qty} onChange={(e) => setQty(Math.max(1, +e.target.value || 1))} />
          <button className="btn" disabled={p.stock < 1} onClick={() => (user ? cart.add(p.id, qty) : nav("/login"))}>
            {p.stock < 1 ? "Out of stock" : "Add to cart"}
          </button>
          <span className="muted small">{p.stock} in stock</span>
        </div>
      </div>
    </div>
  );
}
