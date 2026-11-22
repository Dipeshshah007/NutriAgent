from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # user | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    """Health profile used by the nutrition engine."""
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[int] = mapped_column(Integer, default=30)
    sex: Mapped[str] = mapped_column(String(10), default="male")          # male | female
    height_cm: Mapped[float] = mapped_column(Float, default=170)
    weight_kg: Mapped[float] = mapped_column(Float, default=70)
    activity_level: Mapped[str] = mapped_column(String(20), default="moderate")
    goal: Mapped[str] = mapped_column(String(20), default="maintain")     # lose | maintain | gain
    diet: Mapped[str] = mapped_column(String(30), default="any")          # any|vegetarian|vegan|keto|gluten-free|pescatarian
    allergies: Mapped[list] = mapped_column(JSON, default=list)
    meals_per_day: Mapped[int] = mapped_column(Integer, default=4)

    user: Mapped[User] = relationship(back_populates="profile")


class Product(Base):
    """Generic catalog item: a meal, ingredient, snack, supplement or meal-kit."""
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(60), index=True)
    kind: Mapped[str] = mapped_column(String(30), default="meal")  # meal|snack|ingredient|supplement|drink
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=100)
    image_url: Mapped[str] = mapped_column(String(500), default="")
    serving: Mapped[str] = mapped_column(String(60), default="1 serving")
    calories: Mapped[float] = mapped_column(Float, default=0)
    protein: Mapped[float] = mapped_column(Float, default=0)
    carbs: Mapped[float] = mapped_column(Float, default=0)
    fat: Mapped[float] = mapped_column(Float, default=0)
    fiber: Mapped[float] = mapped_column(Float, default=0)
    meal_types: Mapped[list] = mapped_column(JSON, default=list)  # breakfast|lunch|dinner|snack
    tags: Mapped[list] = mapped_column(JSON, default=list)        # vegan, keto, high-protein ...
    allergens: Mapped[list] = mapped_column(JSON, default=list)   # nuts, dairy, gluten ...
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    product: Mapped[Product] = relationship()


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="paid")  # paid|processing|shipped|delivered|cancelled
    subtotal: Mapped[float] = mapped_column(Float)
    tax: Mapped[float] = mapped_column(Float)
    shipping: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)
    full_name: Mapped[str] = mapped_column(String(120))
    address: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(80))
    zip_code: Mapped[str] = mapped_column(String(20))
    payment_method: Mapped[str] = mapped_column(String(30), default="card")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    user: Mapped[User] = relationship()


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name: Mapped[str] = mapped_column(String(160))
    price: Mapped[float] = mapped_column(Float)
    quantity: Mapped[int] = mapped_column(Integer)
    order: Mapped[Order] = relationship(back_populates="items")


class FoodLog(Base):
    __tablename__ = "food_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    meal_type: Mapped[str] = mapped_column(String(20), default="snack")
    name: Mapped[str] = mapped_column(String(160))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[float] = mapped_column(Float, default=1)
    calories: Mapped[float] = mapped_column(Float, default=0)
    protein: Mapped[float] = mapped_column(Float, default=0)
    carbs: Mapped[float] = mapped_column(Float, default=0)
    fat: Mapped[float] = mapped_column(Float, default=0)


class WeightLog(Base):
    __tablename__ = "weight_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    log_date: Mapped[date] = mapped_column(Date, default=date.today)
    weight_kg: Mapped[float] = mapped_column(Float)


class MealPlan(Base):
    __tablename__ = "meal_plans"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    days: Mapped[int] = mapped_column(Integer, default=7)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
