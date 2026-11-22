from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..ml.nutrition import compute_targets
from ..models import FoodLog, Product, User, WeightLog
from ..schemas import FoodLogIn, FoodLogOut, WeightIn
from ..services import day_totals

router = APIRouter(prefix="/api/tracker", tags=["tracker"])


@router.post("/logs", response_model=FoodLogOut, status_code=201)
def add_log(data: FoodLogIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.product_id:
        p = db.get(Product, data.product_id)
        if not p:
            raise HTTPException(404, "Product not found")
        log = FoodLog(user_id=user.id, product_id=p.id, name=p.name, quantity=data.quantity,
                      calories=p.calories * data.quantity, protein=p.protein * data.quantity,
                      carbs=p.carbs * data.quantity, fat=p.fat * data.quantity)
    else:
        if not data.name or data.calories is None:
            raise HTTPException(422, "Provide a product_id, or a name and calories for a custom food")
        log = FoodLog(user_id=user.id, name=data.name, quantity=data.quantity, calories=data.calories * data.quantity,
                      protein=(data.protein or 0) * data.quantity, carbs=(data.carbs or 0) * data.quantity,
                      fat=(data.fat or 0) * data.quantity)
    log.meal_type = data.meal_type
    log.log_date = data.log_date or date.today()
    db.add(log)
    db.commit()
    return log


@router.get("/logs", response_model=list[FoodLogOut])
def list_logs(day: date | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FoodLog).filter(FoodLog.user_id == user.id, FoodLog.log_date == (day or date.today())).order_by(FoodLog.id).all()


@router.delete("/logs/{log_id}", status_code=204)
def delete_log(log_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    log = db.get(FoodLog, log_id)
    if not log or log.user_id != user.id:
        raise HTTPException(404, "Log not found")
    db.delete(log)
    db.commit()


@router.get("/summary")
def summary(days: int = 7, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    targets = compute_targets(get_profile(db, user))
    history = []
    for i in range(days - 1, -1, -1):
        d = date.today() - timedelta(days=i)
        history.append({"date": d.isoformat(), **day_totals(db, user, d)})
    weights = db.query(WeightLog).filter(WeightLog.user_id == user.id).order_by(WeightLog.log_date.desc()).limit(30).all()
    logged_days = [h for h in history if h["calories"] > 0]
    avg = round(sum(h["calories"] for h in logged_days) / len(logged_days)) if logged_days else 0
    return {"targets": targets, "today": day_totals(db, user), "history": history, "avg_calories": avg,
            "weights": [{"date": w.log_date.isoformat(), "weight_kg": w.weight_kg} for w in reversed(weights)]}


@router.post("/weight", status_code=201)
def add_weight(data: WeightIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    day = data.log_date or date.today()
    entry = db.query(WeightLog).filter_by(user_id=user.id, log_date=day).first()
    if entry:
        entry.weight_kg = data.weight_kg
    else:
        db.add(WeightLog(user_id=user.id, log_date=day, weight_kg=data.weight_kg))
    get_profile(db, user).weight_kg = data.weight_kg  # keep targets in sync with the latest weight
    db.commit()
    return {"ok": True}
