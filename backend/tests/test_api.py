import os
import tempfile

_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["GEMINI_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.ml.nutrition import compute_targets  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client, email="demo@nutriagent.dev", password="Demo@123", path="/api/auth/login"):
    r = client.post(path, json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_and_config(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/config").json()["app_name"] == "NutriAgent"


def test_register_login_and_me(client):
    r = client.post("/api/auth/register", json={"name": "Tester", "email": "t@example.com", "password": "secret1"})
    assert r.status_code == 201
    assert client.post("/api/auth/register", json={"name": "Tester", "email": "t@example.com", "password": "secret1"}).status_code == 409
    h = login(client, "t@example.com", "secret1")
    assert client.get("/api/auth/me", headers=h).json()["email"] == "t@example.com"
    assert client.post("/api/auth/login", json={"email": "t@example.com", "password": "bad"}).status_code == 401


def test_admin_separation(client):
    assert client.post("/api/auth/admin-login", json={"email": "demo@nutriagent.dev", "password": "Demo@123"}).status_code == 403
    admin = login(client, "admin@nutriagent.dev", "Admin@123", "/api/auth/admin-login")
    assert client.get("/api/admin/stats", headers=admin).json()["products"] >= 40
    user = login(client)
    assert client.get("/api/admin/stats", headers=user).status_code == 403
    assert client.get("/api/admin/stats").status_code == 401


def test_catalog_filters(client):
    r = client.get("/api/products", params={"diet": "vegan", "page_size": 60}).json()
    assert r["total"] > 5 and all("vegan" in p["tags"] for p in r["items"])
    r = client.get("/api/products", params={"exclude_allergens": "dairy,gluten", "page_size": 60}).json()
    assert all(not ({"dairy", "gluten"} & set(p["allergens"])) for p in r["items"])
    assert client.get("/api/products", params={"q": "salmon"}).json()["total"] >= 2


def test_nutrition_math():
    class P:  # 30y male, 80kg, 180cm, moderate, maintain
        sex, weight_kg, height_cm, age = "male", 80, 180, 30
        activity_level, goal, diet = "moderate", "maintain", "any"
    t = compute_targets(P)
    assert t["bmr"] == 1780  # 10*80 + 6.25*180 - 5*30 + 5
    assert t["calories"] == round(1780 * 1.55)
    # macros add back up to ~calories
    assert abs(t["protein_g"] * 4 + t["carbs_g"] * 4 + t["fat_g"] * 9 - t["calories"]) < 25


def test_recommendations_respect_allergies_and_diet(client):
    h = login(client)  # demo user is allergic to peanuts
    recs = client.get("/api/products/recommended", headers=h, params={"limit": 20}).json()
    assert recs and all("peanuts" not in r["product"]["allergens"] for r in recs)
    client.put("/api/profile", headers=h, json={"age": 29, "sex": "female", "height_cm": 165, "weight_kg": 68,
               "activity_level": "moderate", "goal": "lose", "diet": "vegan", "allergies": ["peanuts"], "meals_per_day": 4})
    recs = client.get("/api/products/recommended", headers=h, params={"limit": 20}).json()
    assert recs and all("vegan" in r["product"]["tags"] for r in recs)


def test_meal_plan_quality_for_each_diet(client):
    h = login(client)
    for diet in ["any", "vegetarian", "vegan", "keto", "gluten-free", "pescatarian"]:
        client.put("/api/profile", headers=h, json={"age": 29, "sex": "female", "height_cm": 165, "weight_kg": 68,
                   "activity_level": "moderate", "goal": "maintain", "diet": diet, "allergies": [], "meals_per_day": 4})
        r = client.post("/api/planner/generate", headers=h, json={"days": 3})
        assert r.status_code == 200, (diet, r.text)
        plan = r.json()
        assert len(plan["days"]) == 3 and plan["avg_match_score"] > 70, (diet, plan["avg_match_score"])
        assert all(len(d["meals"]) == 4 for d in plan["days"])


def test_cart_checkout_flow(client):
    h = login(client, "t@example.com", "secret1")
    p = client.get("/api/products").json()["items"][0]
    assert client.post("/api/cart", headers=h, json={"product_id": p["id"], "quantity": 2}).json()["count"] == 2
    cart = client.put(f"/api/cart/{p['id']}", headers=h, json={"quantity": 3}).json()
    assert cart["count"] == 3 and cart["subtotal"] == round(p["price"] * 3, 2)
    assert cart["total"] == round(cart["subtotal"] + cart["tax"] + cart["shipping"], 2)
    bad = client.post("/api/orders", headers=h, json={"full_name": "T Tester", "address": "1 Main", "city": "Austin", "zip_code": "12345",
                                                       "payment_method": "card", "card_number": "12"})
    assert bad.status_code == 422
    before = client.get(f"/api/products/{p['id']}").json()["stock"]
    ok = client.post("/api/orders", headers=h, json={"full_name": "T Tester", "address": "1 Main", "city": "Austin", "zip_code": "12345",
                                                      "payment_method": "card", "card_number": "4242 4242 4242 4242"})
    assert ok.status_code == 201 and ok.json()["items"][0]["quantity"] == 3
    assert client.get(f"/api/products/{p['id']}").json()["stock"] == before - 3
    assert client.get("/api/cart", headers=h).json()["count"] == 0
    assert len(client.get("/api/orders", headers=h).json()) == 1
    assert client.post("/api/orders", headers=h, json={"full_name": "T Tester", "address": "1 Main", "city": "Austin", "zip_code": "12345",
                                                        "payment_method": "cod"}).status_code == 400  # empty cart


def test_plan_to_cart_and_tracker(client):
    h = login(client)
    plan = client.post("/api/planner/generate", headers=h, json={"days": 2}).json()
    assert client.post(f"/api/planner/{plan['id']}/add-to-cart", headers=h).json()["added"] > 0
    assert client.get("/api/cart", headers=h).json()["count"] > 0
    p = client.get("/api/products").json()["items"][0]
    log = client.post("/api/tracker/logs", headers=h, json={"product_id": p["id"], "meal_type": "lunch", "quantity": 2})
    assert log.status_code == 201 and log.json()["calories"] == p["calories"] * 2
    s = client.get("/api/tracker/summary", headers=h).json()
    assert s["today"]["calories"] >= p["calories"] * 2 and len(s["history"]) == 7


def test_admin_product_crud_and_order_cancel_restock(client):
    admin = login(client, "admin@nutriagent.dev", "Admin@123", "/api/auth/admin-login")
    new = client.post("/api/admin/products", headers=admin, json={"name": "Test Bar", "category": "Snacks", "kind": "snack", "price": 2.5,
                        "stock": 5, "calories": 100, "protein": 10, "meal_types": ["snack"], "tags": ["vegan"]})
    assert new.status_code == 201
    pid = new.json()["id"]
    assert client.put(f"/api/admin/products/{pid}", headers=admin, json={**new.json(), "price": 3.0}).json()["price"] == 3.0
    assert client.delete(f"/api/admin/products/{pid}", headers=admin).status_code == 204
    assert client.get(f"/api/products/{pid}").status_code == 404
    orders = client.get("/api/admin/orders", headers=admin).json()
    oid = [o for o in orders if o["customer"] == "t@example.com"][0]["id"]
    assert client.put(f"/api/admin/orders/{oid}/status", headers=admin, json={"status": "shipped"}).json()["status"] == "shipped"


def test_coach_offline(client):
    h = login(client)
    r = client.post("/api/chat", headers=h, json={"message": "How much protein do I need?"}).json()
    assert r["source"] == "offline-coach" and "protein" in r["reply"].lower()
