from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..ml import coach
from ..ml.nutrition import compute_targets
from ..ml.recommender import recommend
from ..models import Product, User
from ..schemas import ChatIn, ProfileOut
from ..services import day_totals, history_products

router = APIRouter(prefix="/api/chat", tags=["coach"])


@router.post("")
def chat(data: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = get_profile(db, user)
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    recs = recommend(products, profile, history_products(db, user), top_n=5)
    ctx = {
        "profile": ProfileOut.model_validate(profile).model_dump(),
        "targets": compute_targets(profile),
        "today": day_totals(db, user),
        "recommendations": [{"name": r["product"].name, "calories": round(r["product"].calories),
                             "protein": round(r["product"].protein)} for r in recs],
    }
    return coach.reply(data.message, ctx, [t.model_dump() for t in data.history])
