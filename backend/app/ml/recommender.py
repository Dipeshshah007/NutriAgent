"""Content-based, profile-aware recommender.

Each product becomes a feature vector (macro energy shares, density, tags, kind). The user is
represented by a *preference vector* = blend of
  (a) the ideal macro profile derived from their targets/goal, and
  (b) the centroid of products they previously bought / logged (implicit feedback).
Products are ranked by cosine similarity, after hard filters for diet and allergens.
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from .nutrition import allergen_free, compute_targets, diet_compatible

TAG_VOCAB = ["vegan", "vegetarian", "keto", "gluten-free", "high-protein", "low-carb", "low-calorie",
             "high-fiber", "pescatarian", "heart-healthy", "low-sugar"]
KIND_VOCAB = ["meal", "snack", "ingredient", "supplement", "drink"]


def _macro_shares(cal, protein, carbs, fat):
    total = max(protein * 4 + carbs * 4 + fat * 9, 1e-6)
    return protein * 4 / total, carbs * 4 / total, fat * 9 / total


def product_vector(p) -> np.ndarray:
    ps, cs, fs = _macro_shares(p.calories, p.protein, p.carbs, p.fat)
    fiber_density = min(p.fiber / max(p.calories, 1) * 100, 5) / 5
    kcal = min(p.calories / 800, 1.0)
    tags = [1.0 if t in (p.tags or []) else 0.0 for t in TAG_VOCAB]
    kind = [1.0 if p.kind == k else 0.0 for k in KIND_VOCAB]
    return np.array([ps * 2, cs * 2, fs * 2, fiber_density, kcal, *tags, *kind], dtype=float)


def user_vector(profile, history_products: list) -> np.ndarray:
    t = compute_targets(profile)
    ps, cs, fs = _macro_shares(t["calories"], t["protein_g"], t["carbs_g"], t["fat_g"])
    tags = {k: 0.0 for k in TAG_VOCAB}
    if profile.diet in tags:
        tags[profile.diet] = 1.0
    if profile.diet == "keto":
        tags["low-carb"] = 1.0
    if profile.goal == "lose":
        tags["low-calorie"] = 0.8
        tags["high-fiber"] = 0.5
    if profile.goal in ("lose", "gain"):
        tags["high-protein"] = 1.0
    ideal = np.array([ps * 2, cs * 2, fs * 2, 0.5, 0.45, *tags.values(), 1.0, 0.3, 0.0, 0.0, 0.0], dtype=float)
    if history_products:
        centroid = np.mean([product_vector(p) for p in history_products], axis=0)
        return 0.7 * ideal + 0.3 * centroid
    return ideal


def eligible(products: list, profile) -> list:
    return [p for p in products
            if p.is_active and p.stock > 0
            and diet_compatible(p.tags, profile.diet)
            and allergen_free(p.allergens, profile.allergies)]


def _reasons(p, profile, targets) -> list[str]:
    out = []
    per_meal = targets["calories"] / max(profile.meals_per_day, 1)
    if profile.diet not in ("any", None, ""):
        out.append(f"Fits your {profile.diet} diet")
    if p.protein >= 25 or "high-protein" in (p.tags or []):
        out.append(f"{round(p.protein)}g protein")
    if profile.goal == "lose" and p.calories <= per_meal:
        out.append("Within your per-meal calorie budget")
    if profile.goal == "gain" and p.calories >= per_meal * 0.8:
        out.append("Calorie-dense for your gain goal")
    if p.fiber >= 6:
        out.append(f"{round(p.fiber)}g fiber")
    if profile.allergies:
        out.append("Free of your allergens")
    return out[:3] or ["Balanced nutrition"]


def recommend(products: list, profile, history_products: list | None = None, top_n: int = 8,
              meal_type: str | None = None) -> list[dict]:
    pool = eligible(products, profile)
    if meal_type:
        pool = [p for p in pool if meal_type in (p.meal_types or [])]
    if not pool:
        return []
    targets = compute_targets(profile)
    matrix = np.vstack([product_vector(p) for p in pool])
    sims = cosine_similarity(user_vector(profile, history_products or []).reshape(1, -1), matrix)[0]
    order = np.argsort(-sims)[:top_n]
    return [{"product": pool[i], "score": round(float(sims[i]), 3), "reasons": _reasons(pool[i], profile, targets)}
            for i in order]
