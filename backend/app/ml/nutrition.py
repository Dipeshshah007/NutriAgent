"""Evidence-based nutrition math: BMR (Mifflin-St Jeor), TDEE, goal calories and macro targets."""

ACTIVITY_FACTORS = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "athlete": 1.9}
GOAL_ADJUST = {"lose": -0.20, "maintain": 0.0, "gain": 0.15}
PROTEIN_G_PER_KG = {"lose": 2.0, "maintain": 1.6, "gain": 1.8}

# Diets override the default macro split (fractions of calories: carbs, fat)
DIET_SPLITS = {"keto": {"carbs": 0.08, "fat": 0.65}}


def bmr(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def bmi(weight_kg: float, height_cm: float) -> float:
    m = height_cm / 100
    return round(weight_kg / (m * m), 1) if m else 0.0


def compute_targets(profile) -> dict:
    """Return daily calorie + macro targets for a Profile-like object."""
    b = bmr(profile.sex, profile.weight_kg, profile.height_cm, profile.age)
    tdee = b * ACTIVITY_FACTORS.get(profile.activity_level, 1.55)
    floor = 1500 if profile.sex == "male" else 1200  # never recommend below a safe minimum
    calories = max(floor, tdee * (1 + GOAL_ADJUST.get(profile.goal, 0)))

    protein_g = PROTEIN_G_PER_KG.get(profile.goal, 1.6) * profile.weight_kg
    split = DIET_SPLITS.get(profile.diet)
    if split:
        fat_g = calories * split["fat"] / 9
        carbs_g = calories * split["carbs"] / 4
        protein_g = max(0.0, (calories - fat_g * 9 - carbs_g * 4) / 4)
    else:
        fat_g = calories * 0.27 / 9
        carbs_g = max(0.0, (calories - protein_g * 4 - fat_g * 9) / 4)

    return {
        "bmr": round(b),
        "tdee": round(tdee),
        "bmi": bmi(profile.weight_kg, profile.height_cm),
        "calories": round(calories),
        "protein_g": round(protein_g),
        "carbs_g": round(carbs_g),
        "fat_g": round(fat_g),
        "fiber_g": round(14 * calories / 1000),
    }


def diet_compatible(product_tags: list, diet: str) -> bool:
    tags = set(product_tags or [])
    if diet in (None, "", "any"):
        return True
    if diet == "vegan":
        return "vegan" in tags
    if diet == "vegetarian":
        return bool(tags & {"vegetarian", "vegan"})
    if diet == "pescatarian":
        return bool(tags & {"pescatarian", "vegetarian", "vegan"})
    return diet in tags  # keto, gluten-free, ...


def allergen_free(product_allergens: list, allergies: list) -> bool:
    return not (set(a.lower() for a in (product_allergens or [])) & set(a.lower() for a in (allergies or [])))
