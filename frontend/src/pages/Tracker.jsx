import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { useToast } from "../context.jsx";

function Progress({ label, value, target, unit }) {
  const pct = Math.min(100, (value / Math.max(target, 1)) * 100);
  return (
    <div className="bar-row">
      <div className="row-between small"><span>{label}</span><span>{Math.round(value)} / {target} {unit}</span></div>
      <div className={`bar ${value > target * 1.1 ? "over" : ""}`}><div style={{ width: `${pct}%` }} /></div>
    </div>
  );
}

export default function Tracker() {
  const [sum, setSum] = useState(null);
  const [logs, setLogs] = useState([]);
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState({ meal_type: "lunch", product_id: "", quantity: 1, name: "", calories: "" });
  const [weight, setWeight] = useState("");
  const notify = useToast();

  const load = useCallback(async () => {
    const [s, l] = await Promise.all([api.get("/tracker/summary", { days: 7 }), api.get("/tracker/logs")]);
    setSum(s); setLogs(l);
  }, []);
  useEffect(() => { load(); api.get("/products", { page_size: 60 }).then((r) => setProducts(r.items)); }, [load]);

  const add = async (e) => {
    e.preventDefault();
    try {
      const body = form.product_id
        ? { meal_type: form.meal_type, product_id: +form.product_id, quantity: +form.quantity }
        : { meal_type: form.meal_type, name: form.name, calories: +form.calories, quantity: +form.quantity };
      await api.post("/tracker/logs", body);
      setForm({ ...form, product_id: "", name: "", calories: "", quantity: 1 }); load(); notify("Logged");
    } catch (ex) { notify(ex.message, "err"); }
  };
  const addWeight = async (e) => {
    e.preventDefault();
    try { await api.post("/tracker/weight", { weight_kg: +weight }); setWeight(""); load(); notify("Weight saved"); }
    catch (ex) { notify(ex.message, "err"); }
  };

  if (!sum) return <p className="muted">Loading…</p>;
  const { targets: t, today } = sum;

  return (
    <>
      <h2>Diet tracker</h2>
      <div className="layout cart-layout">
        <section className="card">
          <h3>Today</h3>
          <Progress label="Calories" value={today.calories} target={t.calories} unit="kcal" />
          <Progress label="Protein" value={today.protein} target={t.protein_g} unit="g" />
          <Progress label="Carbs" value={today.carbs} target={t.carbs_g} unit="g" />
          <Progress label="Fat" value={today.fat} target={t.fat_g} unit="g" />
          <h3>Log food</h3>
          <form className="log-form" onSubmit={add}>
            <select value={form.meal_type} onChange={(e) => setForm({ ...form, meal_type: e.target.value })}>
              {["breakfast", "lunch", "dinner", "snack"].map((m) => <option key={m}>{m}</option>)}
            </select>
            <select value={form.product_id} onChange={(e) => setForm({ ...form, product_id: e.target.value })}>
              <option value="">— custom food —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.name} ({Math.round(p.calories)} kcal)</option>)}
            </select>
            {!form.product_id && <>
              <input placeholder="Food name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input type="number" placeholder="kcal" required value={form.calories} onChange={(e) => setForm({ ...form, calories: e.target.value })} />
            </>}
            <input type="number" step="0.5" min="0.5" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} title="servings" />
            <button className="btn sm">Add</button>
          </form>
          <table className="table">
            <tbody>{logs.map((l) => (
              <tr key={l.id}><td><span className="pill">{l.meal_type}</span></td><td>{l.name}{l.quantity !== 1 && ` ×${l.quantity}`}</td>
                <td>{Math.round(l.calories)} kcal</td><td>{Math.round(l.protein)}g P</td>
                <td><button className="link-btn" onClick={async () => { await api.del(`/tracker/logs/${l.id}`); load(); }}>✕</button></td></tr>
            ))}{logs.length === 0 && <tr><td className="muted">Nothing logged today.</td></tr>}</tbody>
          </table>
        </section>

        <aside>
          <div className="card">
            <h3>Last 7 days — calories</h3>
            <div className="chart"><ResponsiveContainer>
              <BarChart data={sum.history.map((h) => ({ ...h, day: h.date.slice(5) }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" /><YAxis width={40} /><Tooltip />
                <ReferenceLine y={t.calories} stroke="#dc2626" strokeDasharray="4 4" label={{ value: "target", fontSize: 11, fill: "#dc2626" }} />
                <Bar dataKey="calories" fill="#16a34a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer></div>
            <p className="muted small">7-day average on logged days: <b>{sum.avg_calories}</b> kcal</p>
          </div>
          <div className="card">
            <h3>Weight trend</h3>
            <div className="chart"><ResponsiveContainer>
              <LineChart data={sum.weights.map((w) => ({ ...w, day: w.date.slice(5) }))}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" /><YAxis width={40} domain={["dataMin - 1", "dataMax + 1"]} /><Tooltip />
                <Line type="monotone" dataKey="weight_kg" stroke="#2563eb" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer></div>
            <form className="log-form" onSubmit={addWeight}>
              <input type="number" step="0.1" placeholder="Today's weight (kg)" required value={weight} onChange={(e) => setWeight(e.target.value)} />
              <button className="btn sm">Save</button>
            </form>
          </div>
        </aside>
      </div>
    </>
  );
}
