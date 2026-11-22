from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Orm = ConfigDict(from_attributes=True)


# ---------- auth ----------
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = Orm
    id: int
    name: str
    email: str
    role: str
    is_active: bool = True
    created_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- profile ----------
class ProfileIn(BaseModel):
    age: int = Field(ge=10, le=100)
    sex: Literal["male", "female"]
    height_cm: float = Field(ge=100, le=250)
    weight_kg: float = Field(ge=30, le=300)
    activity_level: Literal["sedentary", "light", "moderate", "active", "athlete"]
    goal: Literal["lose", "maintain", "gain"]
    diet: Literal["any", "vegetarian", "vegan", "keto", "gluten-free", "pescatarian"]
    allergies: list[str] = []
    meals_per_day: Literal[3, 4, 5] = 4


class ProfileOut(ProfileIn):
    model_config = Orm


# ---------- catalog ----------
class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str = ""
    category: str
    kind: Literal["meal", "snack", "ingredient", "supplement", "drink"] = "meal"
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=100)
    image_url: str = ""
    serving: str = "1 serving"
    calories: float = Field(ge=0, default=0)
    protein: float = Field(ge=0, default=0)
    carbs: float = Field(ge=0, default=0)
    fat: float = Field(ge=0, default=0)
    fiber: float = Field(ge=0, default=0)
    meal_types: list[str] = []
    tags: list[str] = []
    allergens: list[str] = []
    is_active: bool = True


class ProductOut(ProductIn):
    model_config = Orm
    id: int


class RecommendationOut(BaseModel):
    product: ProductOut
    score: float
    reasons: list[str]


# ---------- cart / orders ----------
class CartAddIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=50, default=1)


class CartQtyIn(BaseModel):
    quantity: int = Field(ge=1, le=50)


class CheckoutIn(BaseModel):
    full_name: str = Field(min_length=2)
    address: str = Field(min_length=3)
    city: str = Field(min_length=2)
    zip_code: str = Field(min_length=3)
    payment_method: Literal["card", "cod", "upi"] = "card"
    card_number: str | None = None  # demo only — never stored


class OrderItemOut(BaseModel):
    model_config = Orm
    product_id: int
    name: str
    price: float
    quantity: int


class OrderOut(BaseModel):
    model_config = Orm
    id: int
    status: str
    subtotal: float
    tax: float
    shipping: float
    total: float
    full_name: str
    address: str
    city: str
    zip_code: str
    payment_method: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusIn(BaseModel):
    status: Literal["paid", "processing", "shipped", "delivered", "cancelled"]


# ---------- tracker ----------
class FoodLogIn(BaseModel):
    log_date: date | None = None
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "snack"
    product_id: int | None = None
    name: str | None = None
    quantity: float = Field(gt=0, le=20, default=1)
    calories: float | None = None
    protein: float | None = None
    carbs: float | None = None
    fat: float | None = None


class FoodLogOut(BaseModel):
    model_config = Orm
    id: int
    log_date: date
    meal_type: str
    name: str
    quantity: float
    calories: float
    protein: float
    carbs: float
    fat: float


class WeightIn(BaseModel):
    weight_kg: float = Field(ge=30, le=300)
    log_date: date | None = None


# ---------- planner / chat ----------
class PlanIn(BaseModel):
    days: int = Field(ge=1, le=14, default=7)


class ChatTurn(BaseModel):
    role: Literal["user", "model"]
    text: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = []
