from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import Order, OrderItem, Product, User
from ..schemas import OrderOut, OrderStatusIn, ProductIn, ProductOut, UserOut

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    valid = Order.status != "cancelled"
    revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(valid).scalar()
    since = datetime.utcnow() - timedelta(days=14)
    by_day: dict[str, dict] = {}
    for o in db.query(Order).filter(valid, Order.created_at >= since).all():
        key = o.created_at.date().isoformat()
        by_day.setdefault(key, {"date": key, "revenue": 0.0, "orders": 0})
        by_day[key]["revenue"] += o.total
        by_day[key]["orders"] += 1
    top = (db.query(OrderItem.name, func.sum(OrderItem.quantity).label("qty"))
           .group_by(OrderItem.name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())
    low = db.query(Product).filter(Product.is_active.is_(True), Product.stock <= 10).order_by(Product.stock).limit(8).all()
    return {
        "users": db.query(User).filter(User.role == "user").count(),
        "orders": db.query(Order).count(),
        "products": db.query(Product).filter(Product.is_active.is_(True)).count(),
        "revenue": round(revenue, 2),
        "sales_by_day": [{**v, "revenue": round(v["revenue"], 2)} for _, v in sorted(by_day.items())],
        "top_products": [{"name": n, "quantity": int(q)} for n, q in top],
        "low_stock": [{"id": p.id, "name": p.name, "stock": p.stock} for p in low],
    }


@router.get("/products", response_model=list[ProductOut])
def all_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id.desc()).all()


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: Session = Depends(get_db)):
    p = Product(**data.model_dump())
    db.add(p)
    db.commit()
    return p


@router.put("/products/{pid}", response_model=ProductOut)
def update_product(pid: int, data: ProductIn, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    for k, v in data.model_dump().items():
        setattr(p, k, v)
    db.commit()
    return p


@router.delete("/products/{pid}", status_code=204)
def delete_product(pid: int, db: Session = Depends(get_db)):
    p = db.get(Product, pid)
    if not p:
        raise HTTPException(404, "Product not found")
    p.is_active = False  # soft delete keeps order history intact
    db.commit()


@router.get("/orders")
def all_orders(db: Session = Depends(get_db)):
    out = []
    for o in db.query(Order).order_by(Order.created_at.desc()).limit(200).all():
        d = OrderOut.model_validate(o).model_dump()
        d["customer"] = o.user.email
        out.append(d)
    return out


@router.put("/orders/{oid}/status", response_model=OrderOut)
def set_status(oid: int, data: OrderStatusIn, db: Session = Depends(get_db)):
    o = db.get(Order, oid)
    if not o:
        raise HTTPException(404, "Order not found")
    if data.status == "cancelled" and o.status != "cancelled":
        for it in o.items:  # restock
            p = db.get(Product, it.product_id)
            if p:
                p.stock += it.quantity
    o.status = data.status
    db.commit()
    return o


@router.get("/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.put("/users/{uid}/active", response_model=UserOut)
def toggle_user(uid: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    u = db.get(User, uid)
    if not u:
        raise HTTPException(404, "User not found")
    if u.id == admin.id:
        raise HTTPException(400, "You cannot disable your own account")
    u.is_active = not u.is_active
    db.commit()
    return u
