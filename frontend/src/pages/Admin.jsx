import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { useConfig, useToast } from "../context.jsx";

const csv = (s) => s.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean);
const EMPTY = { name: "", description: "", category: "Lunch", kind: "meal", price: 9.99, stock: 50, serving: "1 serving", calories: 400, protein: 20, carbs: 40, fat: 12, fiber: 5, meal_types: ["lunch"], tags: [], allergens: [], image_url: "", is_active: true };

function Dashboard() {
  const [s, setS] = useState(null);
  const c = useConfig().currency;
  useEffect(() => { api.get("/admin/stats").then(setS); }, []);
  if (!s) return <p className="muted">Loading…</p>;
  return (
    <>
      <div className="stats">
        {[["Revenue", `${c}${s.revenue.toFixed(2)}`], ["Orders", s.orders], ["Customers", s.users], ["Active products", s.products]].map(([l, v]) => (
          <div className="stat" key={l}><div className="v">{v}</div><div className="l">{l}</div></div>
        ))}
      </div>
      <div className="two">
        <div className="card"><h3>Revenue — last 14 days</h3>
          <div className="chart"><ResponsiveContainer><BarChart data={s.sales_by_day.map((d) => ({ ...d, day: d.date.slice(5) }))}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="day" /><YAxis width={45} /><Tooltip />
            <Bar dataKey="revenue" fill="#16a34a" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></div>
        <div className="card"><h3>Top sellers</h3>
          {s.top_products.map((p) => <div className="line" key={p.name}><span>{p.name}</span><b>{p.quantity}</b></div>)}
          <h3>Low stock</h3>
          {s.low_stock.length === 0 ? <p className="muted">All good.</p> : s.low_stock.map((p) => <div className="line" key={p.id}><span>{p.name}</span><b className="danger">{p.stock} left</b></div>)}
        </div>
      </div>
    </>
  );
}

function ProductForm({ initial, onClose, onSaved }) {
  const [f, setF] = useState({ ...initial, tags_s: initial.tags.join(", "), allergens_s: initial.allergens.join(", ") });
  const [err, setErr] = useState("");
  const set = (k, num) => (e) => setF({ ...f, [k]: num ? +e.target.value : e.target.value });
  const toggleMt = (m) => setF({ ...f, meal_types: f.meal_types.includes(m) ? f.meal_types.filter((x) => x !== m) : [...f.meal_types, m] });
  const save = async (e) => {
    e.preventDefault();
    const { tags_s, allergens_s, id, ...rest } = f;
    const body = { ...rest, tags: csv(tags_s), allergens: csv(allergens_s) };
    try { id ? await api.put(`/admin/products/${id}`, body) : await api.post("/admin/products", body); onSaved(); }
    catch (ex) { setErr(ex.message); }
  };
  return (
    <div className="modal-bg" onClick={onClose}>
      <form className="card modal" onClick={(e) => e.stopPropagation()} onSubmit={save}>
        <h3>{f.id ? "Edit product" : "New product"}</h3>
        <div className="form-grid">
          <label className="full">Name<input required value={f.name} onChange={set("name")} /></label>
          <label className="full">Description<input value={f.description} onChange={set("description")} /></label>
          <label>Category<input required value={f.category} onChange={set("category")} /></label>
          <label>Kind<select value={f.kind} onChange={set("kind")}>{["meal", "snack", "ingredient", "supplement", "drink"].map((k) => <option key={k}>{k}</option>)}</select></label>
          <label>Price<input type="number" step="0.01" required value={f.price} onChange={set("price", true)} /></label>
          <label>Stock<input type="number" value={f.stock} onChange={set("stock", true)} /></label>
          <label>Calories<input type="number" value={f.calories} onChange={set("calories", true)} /></label>
          <label>Protein (g)<input type="number" step="0.1" value={f.protein} onChange={set("protein", true)} /></label>
          <label>Carbs (g)<input type="number" step="0.1" value={f.carbs} onChange={set("carbs", true)} /></label>
          <label>Fat (g)<input type="number" step="0.1" value={f.fat} onChange={set("fat", true)} /></label>
          <label>Fibre (g)<input type="number" step="0.1" value={f.fiber} onChange={set("fiber", true)} /></label>
          <label>Serving<input value={f.serving} onChange={set("serving")} /></label>
          <label className="full">Tags (comma separated: vegan, keto, high-protein…)<input value={f.tags_s} onChange={set("tags_s")} /></label>
          <label className="full">Allergens (comma separated)<input value={f.allergens_s} onChange={set("allergens_s")} /></label>
          <div className="full"><div className="lbl">Suitable for meal slots</div>
            <div className="chips">{["breakfast", "lunch", "dinner", "snack"].map((m) => <button type="button" key={m} className={`chip ${f.meal_types.includes(m) ? "on" : ""}`} onClick={() => toggleMt(m)}>{m}</button>)}</div></div>
        </div>
        {err && <div className="alert err">{err}</div>}
        <div className="row-between"><button type="button" className="btn ghost" onClick={onClose}>Cancel</button><button className="btn">Save</button></div>
      </form>
    </div>
  );
}

function Products() {
  const [rows, setRows] = useState([]);
  const [edit, setEdit] = useState(null);
  const notify = useToast();
  const c = useConfig().currency;
  const load = useCallback(() => api.get("/admin/products").then(setRows), []);
  useEffect(() => { load(); }, [load]);
  return (
    <>
      <div className="row-between"><h3>{rows.length} products</h3><button className="btn sm" onClick={() => setEdit(EMPTY)}>+ New product</button></div>
      <div className="card scroll"><table className="table">
        <thead><tr><th>ID</th><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>kcal</th><th>Status</th><th /></tr></thead>
        <tbody>{rows.map((p) => (
          <tr key={p.id} className={p.is_active ? "" : "faded"}>
            <td>{p.id}</td><td>{p.name}</td><td>{p.category}</td><td>{c}{p.price.toFixed(2)}</td>
            <td className={p.stock <= 10 ? "danger" : ""}>{p.stock}</td><td>{Math.round(p.calories)}</td><td>{p.is_active ? "Active" : "Hidden"}</td>
            <td><button className="link-btn" onClick={() => setEdit(p)}>Edit</button>{" "}
              {p.is_active && <button className="link-btn danger" onClick={async () => { if (confirm(`Hide "${p.name}" from the shop?`)) { await api.del(`/admin/products/${p.id}`); load(); notify("Product hidden"); } }}>Delete</button>}</td>
          </tr>))}</tbody>
      </table></div>
      {edit && <ProductForm initial={edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); load(); notify("Saved"); }} />}
    </>
  );
}

function Orders() {
  const [rows, setRows] = useState([]);
  const notify = useToast();
  const c = useConfig().currency;
  const load = useCallback(() => api.get("/admin/orders").then(setRows), []);
  useEffect(() => { load(); }, [load]);
  const setStatus = async (id, status) => {
    try { await api.put(`/admin/orders/${id}/status`, { status }); load(); notify(`Order #${id} → ${status}`); } catch (e) { notify(e.message, "err"); }
  };
  return (
    <div className="card scroll"><table className="table">
      <thead><tr><th>#</th><th>Customer</th><th>Items</th><th>Total</th><th>Date</th><th>Status</th></tr></thead>
      <tbody>{rows.map((o) => (
        <tr key={o.id}><td>{o.id}</td><td>{o.customer}</td><td className="small">{o.items.map((i) => `${i.quantity}× ${i.name}`).join(", ")}</td>
          <td>{c}{o.total.toFixed(2)}</td><td className="small">{new Date(o.created_at + "Z").toLocaleDateString()}</td>
          <td><select value={o.status} onChange={(e) => setStatus(o.id, e.target.value)}>{["paid", "processing", "shipped", "delivered", "cancelled"].map((s) => <option key={s}>{s}</option>)}</select></td></tr>
      ))}</tbody>
    </table></div>
  );
}

function Users() {
  const [rows, setRows] = useState([]);
  const notify = useToast();
  const load = useCallback(() => api.get("/admin/users").then(setRows), []);
  useEffect(() => { load(); }, [load]);
  return (
    <div className="card scroll"><table className="table">
      <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Role</th><th>Joined</th><th>Active</th></tr></thead>
      <tbody>{rows.map((u) => (
        <tr key={u.id}><td>{u.id}</td><td>{u.name}</td><td>{u.email}</td><td>{u.role}</td><td className="small">{u.created_at && new Date(u.created_at + "Z").toLocaleDateString()}</td>
          <td>{u.role === "admin" ? "—" : <button className="link-btn" onClick={async () => { try { await api.put(`/admin/users/${u.id}/active`); load(); } catch (e) { notify(e.message, "err"); } }}>{u.is_active ? "Disable" : "Enable"}</button>}
            {u.role !== "admin" && !u.is_active && <span className="danger small"> disabled</span>}</td></tr>
      ))}</tbody>
    </table></div>
  );
}

export default function Admin() {
  const [tab, setTab] = useState("dashboard");
  const tabs = { dashboard: <Dashboard />, products: <Products />, orders: <Orders />, users: <Users /> };
  return (
    <>
      <h2>Admin panel</h2>
      <div className="tabs">{Object.keys(tabs).map((t) => <button key={t} className={t === tab ? "on" : ""} onClick={() => setTab(t)}>{t[0].toUpperCase() + t.slice(1)}</button>)}</div>
      {tabs[tab]}
    </>
  );
}
