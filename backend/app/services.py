"""Shared helpers used by several routers."""
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .models import CartItem, FoodLog, OrderItem, Order, Product, User


def history_products(db: Session, user: User, limit: int = 30) -> list[Product]:
    """Products the user bought or logged (implicit feedback for the recommender)."""
    ids = [r[0] for r in db.query(OrderItem.product_id).join(Order).filter(Order.user_id == user.id)
           .order_by(Order.created_at.desc()).limit(limit).all()]
    ids += [r[0] for r in db.query(FoodLog.product_id).filter(FoodLog.user_id == user.id, FoodLog.product_id.isnot(None))
            .order_by(FoodLog.id.desc()).limit(limit).all()]
    if not ids:
        return []
    found = {p.id: p for p in db.query(Product).filter(Product.id.in_(set(ids))).all()}
    return [found[i] for i in ids if i in found]


def day_totals(db: Session, user: User, day: date | None = None) -> dict:
    day = day or date.today()
    row = db.query(func.coalesce(func.sum(FoodLog.calories), 0), func.coalesce(func.sum(FoodLog.protein), 0),
                   func.coalesce(func.sum(FoodLog.carbs), 0), func.coalesce(func.sum(FoodLog.fat), 0)
                   ).filter(FoodLog.user_id == user.id, FoodLog.log_date == day).one()
    return {"calories": round(row[0]), "protein": round(row[1], 1), "carbs": round(row[2], 1), "fat": round(row[3], 1)}


def price_breakdown(subtotal: float) -> dict:
    shipping = 0.0 if subtotal == 0 or subtotal >= settings.free_shipping_over else settings.shipping_flat
    tax = round(subtotal * settings.tax_rate, 2)
    return {"subtotal": round(subtotal, 2), "tax": tax, "shipping": round(shipping, 2),
            "total": round(subtotal + tax + shipping, 2)}


def serialize_cart(db: Session, user: User, profile) -> dict:
    from .ml.nutrition import allergen_free, diet_compatible
    rows = db.query(CartItem).filter(CartItem.user_id == user.id).order_by(CartItem.id).all()
    items, subtotal, nutrition, warnings = [], 0.0, {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}, []
    for r in rows:
        p = r.product
        subtotal += p.price * r.quantity
        for k in nutrition:
            nutrition[k] += getattr(p, k) * r.quantity
        if not allergen_free(p.allergens, profile.allergies):
            warnings.append(f"{p.name} contains an allergen from your profile")
        elif not diet_compatible(p.tags, profile.diet):
            warnings.append(f"{p.name} does not match your {profile.diet} diet")
        items.append({"product_id": p.id, "name": p.name, "category": p.category, "price": p.price,
                      "quantity": r.quantity, "stock": p.stock, "line_total": round(p.price * r.quantity, 2),
                      "calories": p.calories, "protein": p.protein})
    return {"items": items, "count": sum(i["quantity"] for i in items),
            "nutrition": {k: round(v) for k, v in nutrition.items()}, "warnings": warnings,
            **price_breakdown(subtotal)}
