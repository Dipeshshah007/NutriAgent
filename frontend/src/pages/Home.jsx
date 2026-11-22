import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import ProductCard from "../components/ProductCard.jsx";
import { useAuth, useConfig } from "../context.jsx";

export default function Home() {
  const cfg = useConfig();
  const { user } = useAuth();
  const [recs, setRecs] = useState([]);
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    if (user && user.role !== "admin") api.get("/products/recommended", { limit: 4 }).then(setRecs).catch(() => {});
    api.get("/products", { sort: "protein_desc", page_size: 4 }).then((r) => setFeatured(r.items)).catch(() => {});
  }, [user]);

  return (
    <>
      <section className="hero">
        <div>
          <h1>Eat for <span>your</span> goals,<br />not the average person's.</h1>
          <p>{cfg.tagline}. We compute your calorie & macro targets, recommend food that fits your diet and allergies, build a weekly plan, and deliver it.</p>
          <div className="hero-cta">
            <Link className="btn" to={user ? "/planner" : "/register"}>{user ? "Build my meal plan" : "Get started free"}</Link>
            <Link className="btn ghost" to="/catalog">Browse the shop</Link>
          </div>
        </div>
        <div className="hero-art">🥗🍳🥑🐟</div>
      </section>

      <section className="steps">
        {[["1", "Profile", "Tell us your body, goal, diet & allergies."],
          ["2", "AI targets", "BMR/TDEE → daily calories & macros."],
          ["3", "Plan & shop", "Optimised weekly plan → one-click cart."],
          ["4", "Track", "Log meals, weight and see progress."]].map(([n, t, d]) => (
          <div className="card step" key={n}><div className="num">{n}</div><h3>{t}</h3><p className="muted">{d}</p></div>
        ))}
      </section>

      {recs.length > 0 && (
        <>
          <h2 className="section">Recommended for you</h2>
          <div className="grid">{recs.map((r) => <ProductCard key={r.product.id} p={r.product} reasons={r.reasons} score={r.score} />)}</div>
        </>
      )}
      <h2 className="section">High-protein favourites</h2>
      <div className="grid">{featured.map((p) => <ProductCard key={p.id} p={p} />)}</div>
    </>
  );
}
