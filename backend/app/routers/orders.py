from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import CartItem, Order, OrderItem, User
from ..schemas import CheckoutIn, OrderOut
from ..services import price_breakdown

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
def checkout(data: CheckoutIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Demo checkout: validates stock, decrements inventory, creates the order atomically.
    No real payment is taken. Swap the marked block for Stripe/Razorpay in production."""
    rows = db.query(CartItem).filter_by(user_id=user.id).all()
    if not rows:
        raise HTTPException(400, "Your cart is empty")
    if data.payment_method == "card":
        digits = "".join(c for c in (data.card_number or "") if c.isdigit())
        if len(digits) < 12:
            raise HTTPException(422, "Enter a valid (demo) card number, e.g. 4242 4242 4242 4242")

    subtotal = 0.0
    for r in rows:
        if not r.product.is_active or r.quantity > r.product.stock:
            raise HTTPException(409, f"'{r.product.name}' is no longer available in that quantity")
        subtotal += r.product.price * r.quantity
    totals = price_breakdown(subtotal)

    # ---- payment gateway integration point (Stripe / Razorpay) would go here ----
    order = Order(user_id=user.id, status="paid", full_name=data.full_name, address=data.address, city=data.city,
                  zip_code=data.zip_code, payment_method=data.payment_method, **totals)
    for r in rows:
        r.product.stock -= r.quantity
        order.items.append(OrderItem(product_id=r.product_id, name=r.product.name, price=r.product.price, quantity=r.quantity))
        db.delete(r)
    db.add(order)
    db.commit()
    return order


@router.get("", response_model=list[OrderOut])
def my_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Order).filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def order_detail(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order or (order.user_id != user.id and user.role != "admin"):
        raise HTTPException(404, "Order not found")
    return order
