from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_profile
from ..models import CartItem, Product, User
from ..schemas import CartAddIn, CartQtyIn
from ..services import serialize_cart

router = APIRouter(prefix="/api/cart", tags=["cart"])


def _out(db, user):
    return serialize_cart(db, user, get_profile(db, user))


@router.get("")
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _out(db, user)


@router.post("")
def add_to_cart(data: CartAddIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    product = db.get(Product, data.product_id)
    if not product or not product.is_active:
        raise HTTPException(404, "Product not found")
    item = db.query(CartItem).filter_by(user_id=user.id, product_id=product.id).first()
    new_qty = (item.quantity if item else 0) + data.quantity
    if new_qty > product.stock:
        raise HTTPException(409, f"Only {product.stock} in stock")
    if item:
        item.quantity = new_qty
    else:
        db.add(CartItem(user_id=user.id, product_id=product.id, quantity=new_qty))
    db.commit()
    return _out(db, user)


@router.put("/{product_id}")
def set_quantity(product_id: int, data: CartQtyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(CartItem).filter_by(user_id=user.id, product_id=product_id).first()
    if not item:
        raise HTTPException(404, "Item not in cart")
    if data.quantity > item.product.stock:
        raise HTTPException(409, f"Only {item.product.stock} in stock")
    item.quantity = data.quantity
    db.commit()
    return _out(db, user)


@router.delete("/{product_id}")
def remove_item(product_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(CartItem).filter_by(user_id=user.id, product_id=product_id).delete()
    db.commit()
    return _out(db, user)


@router.delete("")
def clear_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(CartItem).filter_by(user_id=user.id).delete()
    db.commit()
    return _out(db, user)
