import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useCart, useToast } from "../context.jsx";

const LABEL = { breakfast: "Breakfast", snack_am: "Morning snack", lunch: "Lunch", snack: "Snack", dinner: "Dinner" };

export default function Planner() {
  const [plan, setPlan] = useState(null);
  const [days, setDays] = useState(7);
  const [day, setDay] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const notify = useToast();
  const cart = useCart();
  const nav = useNavigate();

  useEffect(() => { api.get("/planner/latest").then((p) => { setPlan(p); setLoaded(true); }); }, []);

  const generate = async () => {
    setBusy(true);
    try { setPlan(await api.post("/planner/generate", { days })); setDay(0); notify("Meal plan generated"); }
    catch (e) { notify(e.message, "err"); } finally { setBusy(false); }
  };
  const addAll = async () => {
    try {
      const r = await api.post(`/planner/${plan.id}/add-to-cart`);
      await cart.refresh(); notify(`${r.added} items added to cart`); nav("/cart");
    } catch (e) { notify(e.message, "err"); }
  };

  const d = plan?.days?.[day];
  const t = plan?.targets;

  return (
    <>
      <div className="row-between">
        <div>
          <h2>AI Meal Planner</h2>
          <p className="muted">An optimiser picks meals for every slot to land on your calorie & macro targets, with variety — respecting your diet and allergies.</p>
        </div>
        <div className="gen">
          <select value={days} onChange={(e) => setDays(+e.target.value)}>{[3, 5, 7, 10, 14].map((n) => <option key={n} value={n}>{n} days</option>)}</select>
          <button className="btn" onClick={generate} disabled={busy}>{busy ? "Optimising…" : plan ? "Regenerate" : "Generate plan"}</button>
        </div>
      </div>

      {loaded && !plan && <div className="card center">No plan yet. Check your <Link to="/profile">profile</Link>, then press <b>Generate plan</b>.</div>}

      {plan && d && (
        <>
          <div className="row-between">
            <div className="tabs">{plan.days.map((x, i) => <button key={i} className={i === day ? "on" : ""} onClick={() => setDay(i)}>Day {x.day}</button>)}</div>
            <div><span className="pill">Avg match {plan.avg_match_score}%</span> <button className="btn sm" onClick={addAll}>🛒 Add whole plan to cart</button></div>
          </div>
          <div className="layout cart-layout">
            <section>
              {d.meals.map((m) => (
                <div className="card meal" key={m.slot}>
                  <div className="slot">{LABEL[m.slot] || m.slot}</div>
                  <div className="mname"><Link to={`/product/${m.product_id}`}>{m.name}</Link>
                    <div className="muted small">{m.servings} serving{m.servings !== 1 ? "s" : ""} · {m.category}</div></div>
                  <div className="macros"><span><b>{m.calories}</b> kcal</span><span><b>{m.protein}g</b> P</span><span><b>{m.carbs}g</b> C</span><span><b>{m.fat}g</b> F</span></div>
                </div>
              ))}
            </section>
            <aside className="card">
              <h3>Day {d.day} vs target</h3>
              {[["Calories", d.totals.calories, t.calories, "kcal"], ["Protein", d.totals.protein, t.protein_g, "g"], ["Carbs", d.totals.carbs, t.carbs_g, "g"], ["Fat", d.totals.fat, t.fat_g, "g"]].map(([l, v, tg, u]) => (
                <div key={l} className="bar-row">
                  <div className="row-between small"><span>{l}</span><span>{Math.round(v)} / {tg} {u}</span></div>
                  <div className="bar"><div style={{ width: `${Math.min(100, (v / tg) * 100)}%` }} /></div>
                </div>
              ))}
              <p className="muted small">Day match score: <b>{d.match_score}%</b></p>
            </aside>
          </div>
        </>
      )}
    </>
  );
}
