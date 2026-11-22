from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Profile, User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user.id, user.role), user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(name=data.name.strip(), email=email, hashed_password=hash_password(data.password))
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id))
    db.commit()
    return _token(user)


def _authenticate(db: Session, data: LoginIn) -> User:
    user = db.query(User).filter_by(email=data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")
    return user


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    return _token(_authenticate(db, data))


@router.post("/admin-login", response_model=TokenOut)
def admin_login(data: LoginIn, db: Session = Depends(get_db)):
    user = _authenticate(db, data)
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is not an administrator")
    return _token(user)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
