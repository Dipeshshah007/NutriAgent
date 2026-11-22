import { useEffect, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard.jsx";

const DIETS = ["", "vegan", "vegetarian", "keto", "gluten-free", "pescatarian"];
const ALLERGENS = ["dairy", "gluten", "nuts", "peanuts", "egg", "soy", "fish", "shellfish", "sesame"];

export default function Catalog() {
  const [f, setF] = useState({ q: "", category: "", diet: "", sort: "name", max_calories: "", min_protein: "" });
  const [excl, setExcl] = useState([]);
  const [page, setPage] = useState(1);
  const [cats, setCats] = useState([]);
  const [data, setData] = useState({ items: [], total: 0, pages: 1 });
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.get("/categories").then(setCats); }, []);
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => {
      api.get("/products", { ...f, exclude_allergens: excl.join(","), page, page_size: 12 })
        .then(setData).finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [f, excl, page]);

  const set = (k) => (e) => { setF({ ...f, [k]: e.target.value }); setPage(1); };
  const toggle = (a) => { setExcl(excl.includes(a) ? excl.filter((x) => x !== a) : [...excl, a]); setPage(1); };

  return (
    <div className="layout">
      <aside className="card filters">
        <h3>Filters</h3>
        <label>Search<input value={f.q} onChange={set("q")} placeholder="e.g. salmon, curry…" /></label>
        <label>Category
          <select value={f.category} onChange={set("category")}>
            <option value="">All</option>{cats.map((c) => <option key={c}>{c}</option>)}
          </select>
        </label>
        <label>Diet
          <select value={f.diet} onChange={set("diet")}>{DIETS.map((d) => <option key={d} value={d}>{d || "Any"}</option>)}</select>
        </label>
        <label>Max calories<input type="number" value={f.max_calories} onChange={set("max_calories")} placeholder="e.g. 400" /></label>
        <label>Min protein (g)<input type="number" value={f.min_protein} onChange={set("min_protein")} placeholder="e.g. 25" /></label>
        <div className="lbl">Exclude allergens</div>
        <div className="chips">{ALLERGENS.map((a) => (
          <button key={a} className={`chip ${excl.includes(a) ? "on" : ""}`} onClick={() => toggle(a)}>{a}</button>
        ))}</div>
        <button className="btn ghost sm" onClick={() => { setF({ q: "", category: "", diet: "", sort: "name", max_calories: "", min_protein: "" }); setExcl([]); setPage(1); }}>Reset</button>
      </aside>

      <section>
        <div className="toolbar">
          <span className="muted">{data.total} items</span>
          <select value={f.sort} onChange={set("sort")}>
            <option value="name">Name</option><option value="price_asc">Price ↑</option><option value="price_desc">Price ↓</option>
            <option value="calories_asc">Calories ↑</option><option value="protein_desc">Protein ↓</option>
          </select>
        </div>
        {loading ? <p className="muted">Loading…</p> : data.items.length === 0 ? <div className="card center">No items match these filters.</div> : (
          <div className="grid">{data.items.map((p) => <ProductCard key={p.id} p={p} />)}</div>
        )}
        {data.pages > 1 && (
          <div className="pager">
            <button className="btn ghost sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Prev</button>
            <span>Page {page} / {data.pages}</span>
            <button className="btn ghost sm" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>Next →</button>
          </div>
        )}
      </section>
    </div>
  );
}
