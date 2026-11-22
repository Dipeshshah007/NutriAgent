"""Meal-plan optimizer.

For every day we choose one product per meal slot so that the day's totals are as close as possible
to the user's calorie/macro targets. Candidates per slot come from the recommender (so they already
respect diet + allergies), each with an optimal serving size. A small exhaustive search over the
top-K candidates per slot minimises a weighted squared-error loss with a variety penalty so the
same item is not repeated every day.
"""
from __future__ import annotations

import itertools
from collections import Counter

from .nutrition import compute_targets
from .recommender import eligible, recommend

SLOT_SHARE = {
    3: {"breakfast": 0.27, "lunch": 0.37, "dinner": 0.36},
    4: {"breakfast": 0.25, "lunch": 0.33, "dinner": 0.32, "snack": 0.10},
    5: {"breakfast": 0.22, "snack_am": 0.08, "lunch": 0.30, "snack": 0.08, "dinner": 0.32},
}
TOP_K = 6


def _slot_type(slot: str) -> str:
    return "snack" if slot.startswith("snack") else slot


def _candidate(product, slot_kcal: float) -> dict:
    # serving multiplier in 0.25 steps, clamped to a sensible range
    servings = min(2.0, max(0.5, round(slot_kcal / max(product.calories, 1) * 4) / 4))
    return {
        "product": product, "servings": servings,
        "calories": product.calories * servings, "protein": product.protein * servings,
        "carbs": product.carbs * servings, "fat": product.fat * servings,
    }


def _loss(combo: tuple, targets: dict, used: Counter) -> float:
    cal = sum(c["calories"] for c in combo)
    pro = sum(c["protein"] for c in combo)
    carb = sum(c["carbs"] for c in combo)
    fat = sum(c["fat"] for c in combo)
    err = (3.0 * ((cal - targets["calories"]) / targets["calories"]) ** 2
           + 2.0 * ((pro - targets["protein_g"]) / max(targets["protein_g"], 1)) ** 2
           + 1.0 * ((carb - targets["carbs_g"]) / max(targets["carbs_g"], 1)) ** 2
           + 1.0 * ((fat - targets["fat_g"]) / max(targets["fat_g"], 1)) ** 2)
    variety = sum(0.05 * used[c["product"].id] for c in combo)
    dup = 0.5 * (len(combo) - len({c["product"].id for c in combo}))  # same item twice in a day
    return err + variety + dup


def generate_plan(products: list, profile, history_products: list | None = None, days: int = 7) -> dict:
    targets = compute_targets(profile)
    shares = SLOT_SHARE.get(profile.meals_per_day, SLOT_SHARE[4])
    pool_all = eligible(products, profile)
    if not pool_all:
        return {"error": "No catalog items match your diet and allergies.", "days": [], "targets": targets}

    # Rank once per slot type, keep a bigger shortlist so variety is possible across days
    ranked: dict[str, list] = {}
    for slot in shares:
        r = recommend(products, profile, history_products, top_n=TOP_K * 2, meal_type=_slot_type(slot))
        ranked[slot] = [x["product"] for x in r] or [x["product"] for x in recommend(products, profile, history_products, top_n=TOP_K * 2)]

    used: Counter = Counter()
    plan_days = []
    for d in range(days):
        slot_cands = []
        for slot, share in shares.items():
            prods = ranked[slot]
            # rotate the shortlist each day so different items surface, then take top-K
            rot = prods[d % max(len(prods), 1):] + prods[:d % max(len(prods), 1)]
            slot_cands.append([_candidate(p, targets["calories"] * share) for p in rot[:TOP_K]])

        best = min(itertools.product(*slot_cands), key=lambda combo: _loss(combo, targets, used))
        meals = []
        for slot, c in zip(shares, best):
            p = c["product"]
            used[p.id] += 1
            meals.append({
                "slot": slot, "product_id": p.id, "name": p.name, "category": p.category,
                "servings": c["servings"], "price": p.price,
                "calories": round(c["calories"]), "protein": round(c["protein"], 1),
                "carbs": round(c["carbs"], 1), "fat": round(c["fat"], 1),
            })
        tot = {k: round(sum(m[k] for m in meals), 1) for k in ("calories", "protein", "carbs", "fat")}
        cal_err = abs(tot["calories"] - targets["calories"]) / targets["calories"]
        pro_err = abs(tot["protein"] - targets["protein_g"]) / max(targets["protein_g"], 1)
        adherence = max(0, round(100 * (1 - (0.6 * cal_err + 0.4 * pro_err)), 1))
        plan_days.append({"day": d + 1, "meals": meals, "totals": tot, "match_score": adherence})

    avg = round(sum(x["match_score"] for x in plan_days) / len(plan_days), 1)
    return {"days": plan_days, "targets": targets, "avg_match_score": avg, "error": None}
