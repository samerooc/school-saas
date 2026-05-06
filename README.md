# 🏫 SchoolSaaS — Complete School Management Platform

**Stack:** FastAPI + PostgreSQL + React.js + Tailwind CSS  
**Free Hosting:** Railway (backend) + Vercel (frontend) + Supabase (database)  
**Testing Cost: ₹0**

---

## 📁 Project Structure

```
school-saas/
├── backend/              ← FastAPI (deploy to Railway)
│   ├── app/
│   │   ├── main.py       ← App entry point
│   │   ├── core/         ← Config, Security (JWT)
│   │   ├── db/           ← Database session
│   │   ├── models/       ← All DB tables
│   │   ├── api/routes/   ← API endpoints
│   │   ├── schemas/      ← Pydantic request/response models
│   │   ├── services/     ← Business logic
│   │   └── repositories/ ← Database queries
│   ├── alembic/          ← DB migrations
│   ├── keys/             ← RSA keys (generate locally, never commit)
│   ├── requirements.txt
│   ├── .env.example      ← Copy to .env and fill values
│   └── railway.toml      ← Railway deployment config
│
└── frontend/             ← React + Vite (deploy to Vercel)
    ├── src/
    │   ├── App.tsx        ← Main router
    │   ├── pages/         ← Admin, Teacher, Student, Parent portals
    │   ├── stores/        ← Zustand auth store (token in memory)
    │   ├── services/      ← Axios client with auto-refresh
    │   └── components/    ← Reusable UI components
    ├── vercel.json        ← Vercel deployment config
    └── .env.example       ← Copy to .env.local
```

---

## 🚀 STEP-BY-STEP DEPLOYMENT GUIDE

### STEP 1 — Accounts Banao (Sab Free)

1. **GitHub** → https://github.com/signup
2. **Railway** → https://railway.app (GitHub se login karo)
3. **Supabase** → https://supabase.com (GitHub se login karo)
4. **Vercel** → https://vercel.com (GitHub se login karo)

---

### STEP 2 — Code GitHub Pe Upload Karo

```bash
# Terminal/CMD mein yeh commands run karo
cd school-saas

git init
git add .
git commit -m "Initial SchoolSaaS commit"

# GitHub pe new repository banao (school-saas naam se)
# Phir:
git remote add origin https://github.com/YOUR_USERNAME/school-saas.git
git push -u origin main
```

---

### STEP 3 — Supabase Database Setup (Free PostgreSQL)

1. https://supabase.com/dashboard → "New Project" click karo
2. Project name: `school-saas`
3. Password set karo (yaad rakhna!)
4. Region: `South Asia (Mumbai)` select karo
5. "Create new project" click karo — 2 min wait karo

6. **Database URL copy karo:**
   - Left menu → "Settings" → "Database"
   - "Connection string" section mein `URI` tab
   - Copy karo — yeh format mein hoga:
     ```
     postgresql://postgres:YOUR_PASSWORD@db.XXXX.supabase.co:5432/postgres
     ```
7. Asyncpg URL banao (postgresql → postgresql+asyncpg):
   ```
   postgresql+asyncpg://postgres:YOUR_PASSWORD@db.XXXX.supabase.co:5432/postgres
   ```

---

### STEP 4 — Redis Setup (Free — Redis Cloud)

1. https://redis.io/try-free → Sign up
2. "Create database" → Free plan
3. Dashboard mein "Connect" → "RedisInsight" → Copy connection string
4. Format: `redis://default:PASSWORD@redis-xxxxx.redis.cloud:6379`

---

### STEP 5 — RSA Keys Generate Karo (Local Machine Pe)

```bash
cd school-saas/backend

# Windows (Git Bash mein run karo):
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem

# Mac/Linux:
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

⚠️ **private.pem KABHI GitHub pe push mat karo!** (.gitignore mein already add hai)

---

### STEP 6 — Backend Railway Pe Deploy Karo

1. https://railway.app/dashboard → "New Project"
2. "Deploy from GitHub repo" → `school-saas` select karo
3. "backend" folder select karo

4. **Environment Variables add karo** (Railway dashboard → Variables):

```
DATABASE_URL          = postgresql+asyncpg://postgres:PASS@db.XXXX.supabase.co:5432/postgres
DATABASE_URL_SYNC     = postgresql://postgres:PASS@db.XXXX.supabase.co:5432/postgres
REDIS_URL             = redis://default:PASS@redis-xxxxx.redis.cloud:6379
SECRET_KEY            = (random 64 char string — use: python -c "import secrets; print(secrets.token_hex(32))")
APP_ENV               = production
FRONTEND_URL          = https://your-app.vercel.app
ALLOWED_ORIGINS       = https://your-app.vercel.app
JWT_PRIVATE_KEY_PATH  = ./keys/private.pem
JWT_PUBLIC_KEY_PATH   = ./keys/public.pem
```

5. Keys ko Railway mein add karne ke liye:
   - Railway → "Files" tab (agar available ho)
   - Ya Railway CLI use karo:
     ```bash
     npm install -g @railway/cli
     railway login
     railway up
     ```

6. **Deploy hone ke baad** Railway aapko ek URL dega:
   `https://school-saas-production.railway.app`

7. **Test karo:** Browser mein open karo:
   `https://school-saas-production.railway.app/api/health`
   
   Response aana chahiye: `{"status": "ok", "app": "SchoolSaaS"}`

---

### STEP 7 — Database Tables Banao (Migrations)

```bash
# Local machine pe backend folder mein:
cd school-saas/backend
pip install -r requirements.txt

# .env file banao:
cp .env.example .env
# .env mein Supabase URL fill karo

# Migrations run karo:
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

Ya Railway ka "Deploy logs" dekho — railway.toml mein `alembic upgrade head` already add hai, auto-run hoga.

---

### STEP 8 — Frontend Vercel Pe Deploy Karo

1. https://vercel.com/new → GitHub → `school-saas` repo select karo
2. **Framework Preset:** Vite
3. **Root Directory:** `frontend`
4. **Environment Variables add karo:**
   ```
   VITE_API_URL = https://school-saas-production.railway.app/api
   VITE_RAZORPAY_KEY_ID = rzp_test_xxxxxx
   ```
5. "Deploy" click karo

6. **Vercel URL milega:** `https://school-saas-xxxx.vercel.app`

7. Ab Railway mein `FRONTEND_URL` aur `ALLOWED_ORIGINS` update karo Vercel URL se.

---

### STEP 9 — Pehla Admin User Banao

Supabase Dashboard → "SQL Editor" → Run karo:

```sql
-- Pehle ek school banao
INSERT INTO schools (id, name, code, email, phone)
VALUES (
  gen_random_uuid(),
  'My School Name',
  'SCH001',
  'admin@myschool.com',
  '9876543210'
);

-- School ID copy karo from above result, phir admin user banao:
-- Password 'Admin@1234' ka bcrypt hash:
INSERT INTO users (id, school_id, full_name, email, password_hash, role, is_active, is_email_verified)
VALUES (
  gen_random_uuid(),
  'PASTE_SCHOOL_ID_HERE',
  'School Admin',
  'admin@myschool.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY.5mL4Yl7AFMEO',  -- Admin@1234
  'admin',
  true,
  true
);
```

---

### STEP 10 — Test Login

1. Browser mein Vercel URL open karo
2. Login karo:
   - Email: `admin@myschool.com`
   - Password: `Admin@1234`
3. Admin Dashboard dekhna chahiye ✅

---

## 🧪 LOCAL DEVELOPMENT (Bina Deployment Ke Test Karna)

### Backend Local:

```bash
cd school-saas/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Fill in values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

### Frontend Local:

```bash
cd school-saas/frontend
npm install
cp .env.example .env.local
# VITE_API_URL=http://localhost:8000/api
npm run dev
```

Frontend: http://localhost:5173

---

## 🌐 FREE HOSTING SUMMARY

| Service | Platform | URL Format | Free Limit |
|---|---|---|---|
| **Backend** | Railway | `your-app.railway.app` | $5 credit (~500 hrs) |
| **Frontend** | Vercel | `your-app.vercel.app` | Unlimited |
| **Database** | Supabase | Managed PostgreSQL | 500MB, 50K rows |
| **Cache** | Redis Cloud | Managed Redis | 30MB |
| **Files** | Cloudflare R2 | `pub-xxx.r2.dev` | 10GB |
| **Email** | Resend | API | 3,000/month |
| **Push** | Firebase FCM | API | Unlimited |

**Railway free credit khatam hone ke baad:** Render.com use karo — woh bhi free hai (750 hrs/month)

---

## ➕ NEXT MODULES (Is ZIP ke baad)

```
Module 2: Student CRUD + Admission Form
Module 3: Attendance System (Teacher portal)
Module 4: Fee Collection + Razorpay
Module 5: Video LMS (YouTube + Cloudflare)
Module 6: Flutter Mobile App
```

Har module ek alag ZIP mein aayega — simply `/backend` aur `/frontend` folders mein files add karte jao.

---

## ❓ TROUBLESHOOTING

| Problem | Solution |
|---|---|
| Railway deploy fail | Check "Build logs" — usually missing env var |
| `alembic upgrade head` fail | Check DATABASE_URL format — asyncpg vs sync |
| CORS error | Railway mein ALLOWED_ORIGINS update karo |
| Login 401 | Check JWT key paths, ensure keys/ folder uploaded |
| Vercel blank page | Check VITE_API_URL env variable |

---

## 🔐 SECURITY NOTES

- `.env` file kabhi GitHub pe push mat karo
- `keys/private.pem` NEVER commit
- Railway pe env vars directly dashboard se set karo
- Production mein `APP_ENV=production` set karo (docs disable ho jaate hain)
- Default admin password `Admin@1234` immediately change karo after first login
