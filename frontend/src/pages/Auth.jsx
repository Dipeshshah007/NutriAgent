import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth, useConfig } from "../context.jsx";

function AuthForm({ title, subtitle, fields, onSubmit, submitLabel, footer, hint }) {
  const [vals, setVals] = useState({});
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setErr(""); setBusy(true);
    try { await onSubmit(vals); } catch (ex) { setErr(ex.message); } finally { setBusy(false); }
  };
  return (
    <div className="auth-wrap">
      <form className="card auth" onSubmit={submit}>
        <h2>{title}</h2>
        <p className="muted">{subtitle}</p>
        {fields.map(([key, label, type]) => (
          <label key={key}>{label}
            <input type={type} required value={vals[key] || ""} onChange={(e) => setVals({ ...vals, [key]: e.target.value })} />
          </label>
        ))}
        {err && <div className="alert err">{err}</div>}
        <button className="btn block" disabled={busy}>{busy ? "Please wait…" : submitLabel}</button>
        {hint && <div className="hint">{hint}</div>}
        <div className="auth-foot">{footer}</div>
      </form>
    </div>
  );
}

export function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const loc = useLocation();
  return (
    <AuthForm
      title="Welcome back" subtitle="Log in to your account" submitLabel="Log in"
      fields={[["email", "Email", "email"], ["password", "Password", "password"]]}
      onSubmit={async (v) => { const u = await login(v.email, v.password); nav(u.role === "admin" ? "/admin" : loc.state?.from || "/catalog"); }}
      hint={<>Demo: <code>demo@nutriagent.dev</code> / <code>Demo@123</code></>}
      footer={<>New here? <Link to="/register">Create an account</Link></>}
    />
  );
}

export function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  return (
    <AuthForm
      title="Create your account" subtitle="Takes 20 seconds — then set up your health profile" submitLabel="Sign up"
      fields={[["name", "Full name", "text"], ["email", "Email", "email"], ["password", "Password (min 6 chars)", "password"]]}
      onSubmit={async (v) => { await register(v.name, v.email, v.password); nav("/profile"); }}
      footer={<>Already registered? <Link to="/login">Log in</Link></>}
    />
  );
}

export function AdminLogin() {
  const { login } = useAuth();
  const nav = useNavigate();
  const cfg = useConfig();
  return (
    <AuthForm
      title={`${cfg.app_name} Admin`} subtitle="Restricted area — administrators only" submitLabel="Admin log in"
      fields={[["email", "Admin email", "email"], ["password", "Password", "password"]]}
      onSubmit={async (v) => { await login(v.email, v.password, true); nav("/admin"); }}
      hint={<>Demo: <code>admin@nutriagent.dev</code> / <code>Admin@123</code></>}
      footer={<Link to="/login">← Customer login</Link>}
    />
  );
}
