import { useEffect, useState } from "react";
import { api } from "../api";
import { useToast } from "../context.jsx";

const ALLERGENS = ["dairy", "gluten", "nuts", "peanuts", "egg", "soy", "fish", "shellfish", "sesame"];

export function TargetCards({ t }) {
  return (
    <div className="stats">
      {[["Daily calories", t.calories, "kcal"], ["Protein", t.protein_g, "g"], ["Carbs", t.carbs_g, "g"], ["Fat", t.fat_g, "g"], ["BMI", t.bmi, ""], ["BMR", t.bmr, "kcal"]].map(([l, v, u]) => (
        <div className="stat" key={l}><div className="v">{v}<small>{u}</small></div><div className="l">{l}</div></div>
      ))}
    </div>
  );
}

export default function Profile() {
  const [p, setP] = useState(null);
  const [t, setT] = useState(null);
  const notify = useToast();

  useEffect(() => { api.get("/profile").then((d) => { setP(d.profile); setT(d.targets); }); }, []);
  if (!p) return <p className="muted">Loading…</p>;
  const set = (k, num) => (e) => setP({ ...p, [k]: num ? +e.target.value : e.target.value });
  const toggle = (a) => setP({ ...p, allergies: p.allergies.includes(a) ? p.allergies.filter((x) => x !== a) : [...p.allergies, a] });

  const save = async (e) => {
    e.preventDefault();
    try {
      const d = await api.put("/profile", p);
      setP(d.profile); setT(d.targets); notify("Profile saved — targets updated");
    } catch (ex) { notify(ex.message, "err"); }
  };

  return (
    <>
      <h2>Health profile</h2>
      <p className="muted">Your targets are calculated with the Mifflin-St Jeor equation, adjusted for activity and goal.</p>
      {t && <TargetCards t={t} />}
      <form className="card form-grid" onSubmit={save}>
        <label>Age<input type="number" value={p.age} onChange={set("age", true)} /></label>
        <label>Sex<select value={p.sex} onChange={set("sex")}><option>male</option><option>female</option></select></label>
        <label>Height (cm)<input type="number" value={p.height_cm} onChange={set("height_cm", true)} /></label>
        <label>Weight (kg)<input type="number" step="0.1" value={p.weight_kg} onChange={set("weight_kg", true)} /></label>
        <label>Activity level
          <select value={p.activity_level} onChange={set("activity_level")}>
            {["sedentary", "light", "moderate", "active", "athlete"].map((a) => <option key={a}>{a}</option>)}
          </select>
        </label>
        <label>Goal
          <select value={p.goal} onChange={set("goal")}>
            <option value="lose">Lose fat</option><option value="maintain">Maintain</option><option value="gain">Build muscle / gain</option>
          </select>
        </label>
        <label>Diet
          <select value={p.diet} onChange={set("diet")}>
            {["any", "vegetarian", "vegan", "keto", "gluten-free", "pescatarian"].map((d) => <option key={d}>{d}</option>)}
          </select>
        </label>
        <label>Meals per day
          <select value={p.meals_per_day} onChange={set("meals_per_day", true)}><option>3</option><option>4</option><option>5</option></select>
        </label>
        <div className="full">
          <div className="lbl">Allergies (excluded from every recommendation & plan)</div>
          <div className="chips">{ALLERGENS.map((a) => <button type="button" key={a} className={`chip ${p.allergies.includes(a) ? "on" : ""}`} onClick={() => toggle(a)}>{a}</button>)}</div>
        </div>
        <div className="full"><button className="btn">Save profile</button></div>
      </form>
    </>
  );
}
