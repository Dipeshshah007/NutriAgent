import { Link, useNavigate } from "react-router-dom";
import { emojiFor } from "../api";
import { useAuth, useCart, useConfig } from "../context.jsx";

export function Macros({ p }) {
  return (
    <div className="macros">
      <span><b>{Math.round(p.calories)}</b> kcal</span>
      <span><b>{Math.round(p.protein)}g</b> P</span>
      <span><b>{Math.round(p.carbs)}g</b> C</span>
      <span><b>{Math.round(p.fat)}g</b> F</span>
    </div>
  );
}

export default function ProductCard({ p, reasons, score }) {
  const { user } = useAuth();
  const cart = useCart();
  const cfg = useConfig();
  const nav = useNavigate();
  const add = () => (user ? cart.add(p.id, 1) : nav("/login", { state: { from: "/catalog" } }));

  return (
    <div className="card product">
      <Link to={`/product/${p.id}`} className="thumb">{p.image_url ? <img src={p.image_url} alt={p.name} /> : emojiFor(p.category)}</Link>
      <div className="pbody">
        <div className="tags">
          {p.tags.filter((t) => ["vegan", "vegetarian", "keto", "gluten-free", "high-protein"].includes(t)).slice(0, 3).map((t) => (
            <span key={t} className="tag">{t}</span>
          ))}
        </div>
        <Link to={`/product/${p.id}`}><h3>{p.name}</h3></Link>
        <Macros p={p} />
        {reasons && <ul className="reasons">{reasons.map((r) => <li key={r}>✓ {r}</li>)}</ul>}
        {score != null && <div className="match">AI match {Math.round(score * 100)}%</div>}
        <div className="prow">
          <span className="price">{cfg.currency}{p.price.toFixed(2)}</span>
          {p.stock > 0 ? <button className="btn sm" onClick={add}>Add to cart</button> : <span className="oos">Out of stock</span>}
        </div>
      </div>
    </div>
  );
}
