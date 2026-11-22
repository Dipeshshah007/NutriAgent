# 🥗 NutriAgent — AI-Powered Personalized Nutrition & Meal Planning System

A full-stack, white-label platform that turns a person's body, goal, diet and allergies into **calorie/macro targets → ML recommendations → an optimised weekly meal plan → a shopping cart → checkout → daily tracking → an AI coach**. Includes customer and admin portals.

## 2. Run it : Step by Step

### Step 1 — Backend (terminal 1)

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # if blocked:  Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env
```

### Step 2 — Frontend (terminal 2)

```bash
cd frontend
npm install
npm run dev
```
