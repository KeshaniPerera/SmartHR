# SmartHR – Intelligent Attendance & Employee Insight System

A full‑stack HR platform that blends **Django REST APIs**, a **React (Vite) frontend**, and **MongoDB Atlas** to deliver Smart Chat Q&A with NLP, pre‑/post‑hire attrition prediction, performance ranking, and  with face-recognition attendance with lateness detection.

---


## Key Features
- **Smart Chat (NLP)** – Ask HR policy questions in natural language; returns grounded answers.
- **Pre‑hire & Post‑hire screening** – Feature sets for both stages with transparent scoring.
- **Turnover (attrition) risk** – Model‑driven risk flags + reason codes.
- **Performance ranking** – Explainable scores; role‑based visibility.
- **Face‑recognition attendance** (contactless, hygienic) with fallback manual mark.


## Architecture
```
[ React (Vite) SPA ]  <----->  [ Django REST API ]  <----->  [ MongoDB Atlas ]
        |                            |                           |
   Role‑aware UI            Apps: nlp, attendance,         Collections for
   routes (PolicyChat,      prehire, turnover,             employees, accounts,
   Attendance, HR tools)    performance, accounts          policies, predictions
```

## Tech Stack
- **Frontend:** React 19, React Router v7, Tailwind CSS (utility‑first), shadcn/ui
- **Backend:** Django 5, Django REST Framework, PyMongo
- **ML:** scikit‑learn, imbalanced‑learn, pandas, numpy, joblib
- **NLP:** OpenAI API (retrieval‑augmented answers; optionally Atlas Vector Search)
- **DB:** MongoDB Atlas
- **Dev:** python‑dotenv, CORS headers, JWT (SimpleJWT)

## Quick Start
**Prereqs**
- Python ≥ 3.11
- Node.js ≥ 20 & npm (or pnpm)
- A MongoDB Atlas cluster + connection string (SRV)
- (Optional) Tesseract/OpenCV if you enable OCR/vision attendance locally

## Backend Setup (Django)
```bash
cd backend
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
# If you use Django migrations for any relational apps:
# python manage.py migrate

# Create a superuser for admin if needed
# python manage.py createsuperuser
```

## Frontend Setup (React + Vite)
```bash
cd frontend
npm install
# Dev server
npm run dev
# Production build
npm run build
```

## Environment Variables
Create **backend/.env** from the example:
```env
# backend/.env
DEBUG=true
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173
MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/?retryWrites=true&w=majority
MONGODB_DB=smarthr
OPENAI_API_KEY=sk-...
JWT_SECRET=change_me
```
Create **frontend/.env** from the example:
```env
# frontend/.env
VITE_API_BASE=http://localhost:8000/api
```

## Running the Apps
**Backend**
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```
**Frontend**
```bash
cd frontend
npm run dev
```
Open the app at **http://localhost:5173** (frontend). The frontend proxies API calls to **http://localhost:8000/api**.

## Model Artifacts
Store trained models under **backend/models/**, e.g.:
```
models/
├── prehire_model.pkl
├── turnover_model.pkl
├── performance_model.pkl
├── scaler.pkl
└── feature_order.json
```
Load with `joblib.load()` in the corresponding Django app services.


