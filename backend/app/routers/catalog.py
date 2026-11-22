from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..ml.nutrition import allergen_free, diet_compatible
from ..ml.recommender import recommend
from ..models import Product, User
from ..schemas import ProductOut, RecommendationOut
from ..services import history_products

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.query(Product.category).filter(Product.is_active.is_(True)).distinct().all()
    return sorted(r[0] for r in rows)


@router.get("/products")
def list_products(
    q: str = "", category: str = "", kind: str = "", diet: str = "",
    exclude_allergens: str = Query("", description="comma separated"),
    max_calories: float | None = None, min_protein: float | None = None,
    sort: str = Query("name", pattern="^(name|price_asc|price_desc|calories_asc|protein_desc)$"),
    page: int = Query(1, ge=1), page_size: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))
    if q:
        like = f"%{q.lower()}%"
        from sqlalchemy import func, or_
        query = query.filter(or_(func.lower(Product.name).like(like), func.lower(Product.description).like(like)))
    if category:
        query = query.filter(Product.category == category)
    if kind:
        query = query.filter(Product.kind == kind)
    if max_calories is not None:
        query = query.filter(Product.calories <= max_calories)
    if min_protein is not None:
        query = query.filter(Product.protein >= min_protein)
    order = {"name": Product.name, "price_asc": Product.price, "price_desc": Product.price.desc(),
             "calories_asc": Product.calories, "protein_desc": Product.protein.desc()}[sort]
    rows = query.order_by(order).all()
    # JSON-column filters (tags/allergens) are applied in Python so the code is portable across SQLite & Postgres
    allergens = [a.strip() for a in exclude_allergens.split(",") if a.strip()]
    rows = [p for p in rows if (not diet or diet_compatible(p.tags, diet)) and allergen_free(p.allergens, allergens)]
    total = len(rows)
    start = (page - 1) * page_size
    return {"items": [ProductOut.model_validate(p) for p in rows[start:start + page_size]],
            "total": total, "page": page, "pages": max(1, -(-total // page_size))}


@router.get("/products/recommended", response_model=list[RecommendationOut])
def recommended(meal_type: str | None = None, limit: int = Query(8, ge=1, le=24),
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = get_profile(db, user)
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    return recommend(products, profile, history_products(db, user), top_n=limit, meal_type=meal_type)


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p or not p.is_active:
        raise HTTPException(404, "Product not found")
    return p
