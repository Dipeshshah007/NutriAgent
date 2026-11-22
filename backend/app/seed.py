"""Seed data: admin + demo accounts, a 47-item catalog and some demo history for dashboards."""
import random
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from .config import settings
from .models import FoodLog, Order, OrderItem, Product, Profile, User, WeightLog
from .security import hash_password

B, L, D, S = "breakfast", "lunch", "dinner", "snack"

# name, category, kind, meal_types, kcal, protein, carbs, fat, fiber, price, tags, allergens, serving, description
CATALOG = [
    ("Greek Yogurt Berry Parfait", "Breakfast", "meal", [B, S], 280, 22, 34, 6, 4, 5.99, ["vegetarian", "high-protein", "gluten-free"], ["dairy"], "1 cup", "Thick Greek yogurt layered with mixed berries and crunchy seeds."),
    ("Veggie Egg-White Scramble", "Breakfast", "meal", [B], 260, 28, 10, 12, 3, 6.49, ["vegetarian", "high-protein", "keto", "low-carb", "gluten-free"], ["egg"], "1 plate", "Fluffy egg whites with spinach, peppers and mushrooms."),
    ("Overnight Oats with Chia", "Breakfast", "meal", [B], 340, 12, 52, 9, 9, 4.99, ["vegan", "high-fiber"], ["gluten"], "1 jar", "Rolled oats soaked in oat milk with chia and banana."),
    ("Tofu Scramble Breakfast Bowl", "Breakfast", "meal", [B], 310, 24, 22, 14, 6, 6.99, ["vegan", "high-protein", "gluten-free"], ["soy"], "1 bowl", "Turmeric tofu scramble with sweet potato and greens."),
    ("Avocado Egg Toast", "Breakfast", "meal", [B], 380, 16, 30, 22, 8, 5.49, ["vegetarian"], ["gluten", "egg"], "2 slices", "Sourdough, smashed avocado and a soft-poached egg."),
    ("Keto Avocado Bacon Egg Cups", "Breakfast", "meal", [B], 420, 24, 6, 33, 4, 7.49, ["keto", "low-carb", "gluten-free"], ["egg"], "3 cups", "Baked egg cups with avocado and crispy turkey bacon."),
    ("Banana-Oat Protein Pancakes", "Breakfast", "meal", [B], 360, 26, 48, 7, 5, 5.99, ["vegetarian", "high-protein"], ["egg", "gluten", "dairy"], "3 pancakes", "High-protein pancakes sweetened only with banana."),
    ("Chia Coconut Pudding", "Breakfast", "meal", [B, S], 290, 8, 22, 19, 11, 4.99, ["vegan", "gluten-free", "high-fiber", "low-sugar"], [], "1 cup", "Creamy chia pudding with coconut milk and toasted flakes."),
    ("Grilled Chicken Quinoa Bowl", "Lunch", "meal", [L, D], 520, 42, 52, 14, 8, 9.99, ["high-protein", "gluten-free", "heart-healthy"], [], "1 bowl", "Grilled chicken, quinoa, roasted veg and lemon-herb dressing."),
    ("Mediterranean Chickpea Salad", "Lunch", "meal", [L], 430, 18, 52, 16, 14, 8.49, ["vegan", "gluten-free", "high-fiber", "heart-healthy"], [], "1 bowl", "Chickpeas, cucumber, tomato, olives and olive-oil vinaigrette."),
    ("Turkey & Avocado Wrap", "Lunch", "meal", [L], 480, 34, 42, 18, 7, 8.99, ["high-protein"], ["gluten"], "1 wrap", "Sliced turkey, avocado, greens in a whole-wheat wrap."),
    ("Tuna Poke Bowl", "Lunch", "meal", [L, D], 490, 38, 52, 13, 5, 10.99, ["pescatarian", "high-protein", "gluten-free"], ["fish", "soy"], "1 bowl", "Ahi tuna over brown rice with edamame and sesame."),
    ("Keto Chicken Caesar Salad", "Lunch", "meal", [L], 460, 40, 6, 31, 3, 9.49, ["keto", "low-carb", "gluten-free", "high-protein"], ["dairy", "egg", "fish"], "1 bowl", "Grilled chicken, romaine, parmesan — croutons left out."),
    ("Lentil & Sweet Potato Curry", "Lunch", "meal", [L, D], 450, 20, 70, 9, 16, 8.49, ["vegan", "gluten-free", "high-fiber", "heart-healthy"], [], "1 bowl", "Slow-cooked red lentils and sweet potato in mild curry."),
    ("Falafel Hummus Plate", "Lunch", "meal", [L, D], 540, 20, 62, 24, 14, 8.99, ["vegan", "high-fiber"], ["sesame"], "1 plate", "Baked falafel, hummus, tabbouleh and pickled veg."),
    ("Veggie Buddha Bowl with Tahini", "Lunch", "meal", [L], 410, 15, 55, 15, 12, 8.49, ["vegan", "gluten-free", "high-fiber"], ["sesame"], "1 bowl", "Roasted vegetables, brown rice, chickpeas, tahini drizzle."),
    ("Egg Salad Lettuce Wraps", "Lunch", "meal", [L], 380, 24, 8, 28, 2, 7.49, ["vegetarian", "keto", "low-carb", "gluten-free"], ["egg"], "3 wraps", "Creamy egg salad in crisp butter-lettuce cups."),
    ("Baked Salmon with Asparagus", "Dinner", "meal", [D], 520, 44, 10, 34, 4, 13.49, ["pescatarian", "keto", "low-carb", "gluten-free", "high-protein", "heart-healthy"], ["fish"], "1 plate", "Oven-baked salmon fillet with lemon and asparagus."),
    ("Lean Beef Stir-Fry with Brown Rice", "Dinner", "meal", [D], 580, 42, 60, 18, 6, 11.49, ["high-protein"], ["soy"], "1 plate", "Lean beef strips and crisp vegetables over brown rice."),
    ("Zucchini Noodles Turkey Bolognese", "Dinner", "meal", [D], 430, 38, 20, 22, 5, 9.99, ["low-carb", "gluten-free", "high-protein"], [], "1 bowl", "Spiralised zucchini with slow-simmered turkey bolognese."),
    ("Tofu Veggie Stir-Fry", "Dinner", "meal", [D], 400, 26, 38, 16, 8, 8.99, ["vegan", "high-protein"], ["soy"], "1 plate", "Crispy tofu and seasonal vegetables in ginger-garlic sauce."),
    ("Herb Roasted Chicken & Vegetables", "Dinner", "meal", [D], 480, 46, 22, 22, 6, 10.49, ["high-protein", "gluten-free"], [], "1 plate", "Roasted chicken thigh with root vegetables and rosemary."),
    ("Shrimp & Veggie Skillet", "Dinner", "meal", [D], 380, 40, 16, 16, 4, 11.99, ["pescatarian", "low-carb", "gluten-free", "high-protein", "low-calorie"], ["shellfish"], "1 skillet", "Garlic shrimp sautéed with zucchini, peppers and tomatoes."),
    ("Black Bean Burrito Bowl", "Dinner", "meal", [D, L], 560, 22, 88, 14, 20, 8.49, ["vegan", "gluten-free", "high-fiber"], [], "1 bowl", "Black beans, rice, corn salsa, guacamole and lime."),
    ("Mushroom Spinach Lasagna", "Dinner", "meal", [D], 510, 28, 48, 22, 6, 9.99, ["vegetarian"], ["dairy", "gluten", "egg"], "1 slice", "Layers of mushroom, spinach, ricotta and tomato sauce."),
    ("Keto Ribeye with Garlic Broccoli", "Dinner", "meal", [D], 640, 45, 8, 48, 4, 15.99, ["keto", "low-carb", "gluten-free", "high-protein"], ["dairy"], "1 plate", "Pan-seared ribeye with garlic-butter broccoli."),
    ("Chickpea Coconut Curry", "Dinner", "meal", [D, L], 470, 16, 58, 20, 13, 8.49, ["vegan", "gluten-free", "high-fiber"], [], "1 bowl", "Chickpeas simmered in coconut-tomato curry."),
    ("Almond Butter Energy Bites", "Snacks", "snack", [S], 240, 7, 22, 15, 4, 4.49, ["vegan", "gluten-free"], ["nuts"], "4 bites", "Oats-free bites of almond butter, dates and cacao."),
    ("Roasted Chickpeas", "Snacks", "snack", [S], 140, 7, 20, 4, 6, 2.99, ["vegan", "gluten-free", "high-fiber", "low-calorie"], [], "1 bag", "Crunchy oven-roasted chickpeas with smoked paprika."),
    ("Cottage Cheese & Pineapple Cup", "Snacks", "snack", [S], 150, 16, 14, 3, 1, 3.49, ["vegetarian", "high-protein", "gluten-free", "low-calorie"], ["dairy"], "1 cup", "Low-fat cottage cheese with pineapple chunks."),
    ("Hard-Boiled Eggs (3-pack)", "Snacks", "snack", [S], 210, 18, 1, 15, 0, 2.99, ["vegetarian", "keto", "low-carb", "gluten-free", "high-protein"], ["egg"], "3 eggs", "Free-range eggs, peeled and ready to eat."),
    ("Mixed Nuts & Seeds", "Snacks", "snack", [S], 200, 6, 8, 17, 3, 3.99, ["vegan", "keto", "low-carb", "gluten-free"], ["nuts"], "40 g", "Almonds, walnuts, pumpkin and sunflower seeds."),
    ("Apple Slices with Peanut Butter", "Snacks", "snack", [S], 190, 6, 24, 9, 5, 3.29, ["vegan", "gluten-free"], ["peanuts"], "1 pack", "Crisp apple wedges with single-serve peanut butter."),
    ("Dark Chocolate Protein Bar", "Snacks", "snack", [S], 210, 20, 22, 7, 5, 2.99, ["vegetarian", "high-protein"], ["dairy", "soy", "nuts"], "1 bar", "20 g protein, 4 g sugar, no artificial sweeteners."),
    ("Veggie Sticks & Hummus", "Snacks", "snack", [S], 160, 6, 18, 8, 6, 3.49, ["vegan", "gluten-free", "low-calorie"], ["sesame"], "1 pack", "Carrot, celery and pepper sticks with classic hummus."),
    ("Crunchy Cheese Crisps", "Snacks", "snack", [S], 150, 12, 1, 11, 0, 3.49, ["vegetarian", "keto", "low-carb", "gluten-free"], ["dairy"], "1 bag", "Baked parmesan crisps — all crunch, no carbs."),
    ("Cold-Pressed Green Juice", "Drinks", "drink", [S], 90, 2, 20, 0, 2, 5.99, ["vegan", "gluten-free", "low-calorie"], [], "355 ml", "Kale, cucumber, apple, lemon and ginger."),
    ("Unsweetened Almond Milk 1L", "Drinks", "drink", [], 30, 1, 1, 2.5, 0, 3.49, ["vegan", "keto", "gluten-free", "low-calorie"], ["nuts"], "1 cup", "Creamy, unsweetened dairy-free milk."),
    ("Whey Protein Isolate - Vanilla", "Supplements", "supplement", [], 120, 25, 2, 1, 0, 29.99, ["vegetarian", "high-protein", "gluten-free", "low-carb"], ["dairy"], "1 scoop", "Fast-absorbing isolate, 25 g protein per scoop."),
    ("Plant Protein Powder - Pea", "Supplements", "supplement", [], 110, 22, 3, 2, 2, 27.99, ["vegan", "high-protein", "gluten-free", "low-carb"], [], "1 scoop", "Pea & rice blend, complete amino acid profile."),
    ("Omega-3 Fish Oil (60 caps)", "Supplements", "supplement", [], 10, 0, 0, 1, 0, 18.99, ["pescatarian", "gluten-free", "heart-healthy"], ["fish"], "2 caps", "Triple-strength EPA/DHA, third-party tested."),
    ("Daily Multivitamin (90 tabs)", "Supplements", "supplement", [], 5, 0, 1, 0, 0, 12.99, ["vegan", "gluten-free"], [], "1 tab", "Complete daily multivitamin and mineral complex."),
    ("Organic Quinoa 1 kg", "Pantry", "ingredient", [], 120, 4.4, 21, 1.9, 2.8, 7.99, ["vegan", "gluten-free"], [], "100 g cooked", "Pre-rinsed tri-colour quinoa."),
    ("Extra Virgin Olive Oil 500 ml", "Pantry", "ingredient", [], 120, 0, 0, 14, 0, 12.99, ["vegan", "keto", "gluten-free", "heart-healthy"], [], "1 tbsp", "Cold-pressed, single-origin olive oil."),
    ("Wild Salmon Fillets (4 pack)", "Fresh", "ingredient", [], 280, 34, 0, 15, 0, 16.99, ["pescatarian", "keto", "low-carb", "gluten-free", "high-protein"], ["fish"], "1 fillet", "Sustainably caught, skin-on, individually frozen."),
    ("Chicken Breast 1 kg", "Fresh", "ingredient", [], 165, 31, 0, 3.6, 0, 8.99, ["high-protein", "low-carb", "keto", "gluten-free"], [], "100 g", "Skinless, boneless free-range chicken breast."),
]


def _profile(user_id, **kw):
    return Profile(user_id=user_id, **kw)


def seed(db: Session) -> None:
    if not db.query(User).filter_by(email=settings.admin_email).first():
        db.add(User(name="Store Admin", email=settings.admin_email,
                    hashed_password=hash_password(settings.admin_password), role="admin"))
        db.flush()

    demo = db.query(User).filter_by(email=settings.demo_email).first()
    is_new_demo = demo is None
    if is_new_demo:
        demo = User(name="Demo User", email=settings.demo_email, hashed_password=hash_password(settings.demo_password))
        db.add(demo)
        db.flush()
        db.add(_profile(demo.id, age=29, sex="female", height_cm=165, weight_kg=68, activity_level="moderate",
                        goal="lose", diet="any", allergies=["peanuts"], meals_per_day=4))

    if db.query(Product).count() == 0:
        for i, (name, cat, kind, mts, kcal, p, c, f, fib, price, tags, alg, serving, desc) in enumerate(CATALOG):
            db.add(Product(name=name, category=cat, kind=kind, meal_types=mts, calories=kcal, protein=p, carbs=c,
                           fat=f, fiber=fib, price=price, tags=tags, allergens=alg, serving=serving,
                           description=desc, stock=8 if i % 13 == 0 else 40 + (i * 7) % 120))
        db.flush()

    if is_new_demo:  # demo history so dashboards/charts look alive
        rnd = random.Random(7)
        products = db.query(Product).filter(Product.kind.in_(["meal", "snack"])).all()
        for d in range(1, 15):
            when = datetime.utcnow() - timedelta(days=d, hours=rnd.randint(0, 10))
            chosen = rnd.sample(products, rnd.randint(1, 3))
            sub = sum(p.price for p in chosen)
            ship = 0 if sub >= settings.free_shipping_over else settings.shipping_flat
            tax = round(sub * settings.tax_rate, 2)
            o = Order(user_id=demo.id, status="delivered", subtotal=round(sub, 2), tax=tax, shipping=ship,
                      total=round(sub + tax + ship, 2), full_name="Demo User", address="12 Green St",
                      city="Austin", zip_code="73301", payment_method="card", created_at=when)
            o.items = [OrderItem(product_id=p.id, name=p.name, price=p.price, quantity=1) for p in chosen]
            db.add(o)
        for d in range(0, 7):
            day = date.today() - timedelta(days=d)
            for slot, p in zip([B, L, D, S], rnd.sample(products, 4)):
                if p.allergens and "peanuts" in p.allergens:
                    continue
                db.add(FoodLog(user_id=demo.id, log_date=day, meal_type=slot, name=p.name, product_id=p.id,
                               quantity=1, calories=p.calories, protein=p.protein, carbs=p.carbs, fat=p.fat))
            db.add(WeightLog(user_id=demo.id, log_date=day, weight_kg=round(68.6 - (6 - d) * 0.12 + rnd.uniform(-0.2, 0.2), 1)))
    db.commit()
