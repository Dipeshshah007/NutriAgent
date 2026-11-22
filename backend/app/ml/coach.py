"""AI nutrition coach.

* If GEMINI_API_KEY is set -> calls Google's free-tier Gemini API with the user's real data as context
  (grounded generation: the LLM only sees structured facts computed by our own engine).
* Otherwise (or on any API error) -> a deterministic offline coach, so the app always works for free.
"""
from __future__ import annotations

import httpx

from ..config import settings

DISCLAIMER = "This is general wellness guidance, not medical advice."


def _context_block(ctx: dict) -> str:
    t, today = ctx["targets"], ctx["today"]
    p = ctx["profile"]
    recs = ", ".join(f"{r['name']} ({r['calories']} kcal, {r['protein']}g protein)" for r in ctx["recommendations"][:5])
    return (
        f"User profile: {p['age']}y {p['sex']}, {p['height_cm']}cm, {p['weight_kg']}kg, goal={p['goal']}, "
        f"diet={p['diet']}, allergies={p['allergies'] or 'none'}.\n"
        f"Daily targets: {t['calories']} kcal, {t['protein_g']}g protein, {t['carbs_g']}g carbs, {t['fat_g']}g fat.\n"
        f"Eaten today: {today['calories']} kcal, {today['protein']}g protein, {today['carbs']}g carbs, {today['fat']}g fat.\n"
        f"Catalog items recommended for this user: {recs}."
    )


def _gemini(message: str, ctx: dict, history: list[dict]) -> str | None:
    if not settings.gemini_api_key:
        return None
    system = ("You are NutriAgent, a friendly, concise nutrition coach inside a meal-planning store. "
              "Use ONLY the facts provided for numbers. Prefer recommending items from the catalog list. "
              "Never diagnose or give medical treatment advice. Keep answers under 140 words.\n\n" + _context_block(ctx))
    contents = [{"role": "user" if h["role"] == "user" else "model", "parts": [{"text": h["text"]}]} for h in history[-6:]]
    contents.append({"role": "user", "parts": [{"text": message}]})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    try:
        r = httpx.post(url, params={"key": settings.gemini_api_key}, timeout=20,
                       json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents})
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


def _offline(message: str, ctx: dict) -> str:
    m = message.lower()
    t, today, p = ctx["targets"], ctx["today"], ctx["profile"]
    recs = ctx["recommendations"]
    left_cal = t["calories"] - today["calories"]
    left_pro = t["protein_g"] - today["protein"]

    def top(n=3):
        return "; ".join(f"{r['name']} ({r['calories']} kcal, {r['protein']}g P)" for r in recs[:n]) or "nothing matches your filters yet"

    if any(w in m for w in ("hello", "hi ", "hey")) or m.strip() in ("hi", "hello", "hey"):
        return f"Hi! I'm your NutriAgent coach. Your daily goal is {t['calories']} kcal and {t['protein_g']}g protein. Ask me what to eat, how you're doing today, or how to reach your goal."
    if any(w in m for w in ("left", "remaining", "today", "progress", "how am i")):
        return (f"So far today: {today['calories']} of {t['calories']} kcal and {today['protein']} of {t['protein_g']}g protein. "
                f"That leaves about {max(0, left_cal)} kcal and {max(0, round(left_pro))}g protein.")
    if "protein" in m:
        return f"Your protein target is {t['protein_g']}g/day ({round(t['protein_g'] / p['weight_kg'], 1)} g/kg). Good picks from the catalog: {top()}."
    if any(w in m for w in ("calorie", "kcal", "bmr", "tdee")):
        return f"Your BMR is ~{t['bmr']} kcal and maintenance (TDEE) ~{t['tdee']} kcal. For your '{p['goal']}' goal the target is {t['calories']} kcal/day."
    if any(w in m for w in ("eat", "recommend", "suggest", "dinner", "lunch", "breakfast", "snack", "meal", "hungry")):
        return f"Based on your goal ({p['goal']}) and {p['diet']} diet, try: {top()}. Open the Meal Planner for a full week."
    if any(w in m for w in ("lose", "weight", "fat", "cut")):
        return (f"For fat loss we use a ~20% deficit ({t['calories']} kcal), high protein ({t['protein_g']}g) to protect muscle, and fibre-rich foods. "
                f"Aim for 0.25–0.5 kg loss per week. Try: {top()}.")
    if any(w in m for w in ("gain", "muscle", "bulk")):
        return f"For lean gain we use a ~15% surplus ({t['calories']} kcal) with {t['protein_g']}g protein. Try: {top()}."
    return (f"I can help with calories, protein, what to eat, and tracking. Today you've had {today['calories']} kcal of {t['calories']}. "
            f"Try asking: 'What should I eat for dinner?'")


def reply(message: str, ctx: dict, history: list[dict] | None = None) -> dict:
    text = _gemini(message, ctx, history or [])
    source = "gemini"
    if text is None:
        text, source = _offline(message, ctx), "offline-coach"
    return {"reply": f"{text}\n\n_{DISCLAIMER}_", "source": source}
