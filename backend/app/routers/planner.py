from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..ml.planner import generate_plan
from ..models import CartItem, MealPlan, Product, User
from ..schemas import PlanIn
from ..services import history_products

router = APIRouter(prefix="/api/planner", tags=["planner"])


def _plannable(db: Session) -> list[Product]:
    return db.query(Product).filter(Product.is_active.is_(True), Product.kind.in_(["meal", "snack", "drink"])).all()


@router.post("/generate")
def generate(data: PlanIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = get_profile(db, user)
    result = generate_plan(_plannable(db), profile, history_products(db, user), days=data.days)
    if result["error"]:
        raise HTTPException(422, result["error"])
    plan = MealPlan(user_id=user.id, days=data.days, data=result)
    db.add(plan)
    db.commit()
    return {"id": plan.id, "created_at": plan.created_at, **result}


@router.get("/latest")
def latest(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = db.query(MealPlan).filter_by(user_id=user.id).order_by(MealPlan.id.desc()).first()
    if not plan:
        return None
    return {"id": plan.id, "created_at": plan.created_at, **plan.data}


@router.post("/{plan_id}/add-to-cart")
def plan_to_cart(plan_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """One click: turn a meal plan into a shopping cart (round servings up to whole units)."""
    plan = db.get(MealPlan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(404, "Plan not found")
    needed: dict[int, int] = {}
    for day in plan.data["days"]:
        for m in day["meals"]:
            needed[m["product_id"]] = needed.get(m["product_id"], 0) + 1
    added, skipped = 0, []
    for pid, qty in needed.items():
        p = db.get(Product, pid)
        if not p or not p.is_active or p.stock <= 0:
            skipped.append(pid)
            continue
        qty = min(qty, p.stock)
        item = db.query(CartItem).filter_by(user_id=user.id, product_id=pid).first()
        if item:
            item.quantity = min(item.quantity + qty, p.stock)
        else:
            db.add(CartItem(user_id=user.id, product_id=pid, quantity=qty))
        added += 1
    db.commit()
    return {"added": added, "skipped": skipped}
