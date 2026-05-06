# 🚀 SchoolSaaS — Production Deployment Guide
## Module 5 Complete | All Modules: 1–5

---

## 📦 WHAT'S IN THIS ZIP

```
school-saas/
├── backend/          → FastAPI (Railway)       ← All 5 modules complete
├── frontend/         → React + Vite (Vercel)   ← All portals + public website
└── mobile/           → Flutter App             ← Android + iOS
```

### Backend APIs (v5.0):
- ✅ Auth (JWT RS256, refresh tokens, RBAC)
- ✅ Students (CRUD, premium, photo upload)
- ✅ Staff (CRUD, employee management)
- ✅ Classes + Subjects + Academic Year
- ✅ Attendance (bulk mark, reports)
- ✅ Homework + Notices
- ✅ Video LMS (YouTube paste + Cloudflare backup)
- ✅ Fee Management + Razorpay
- ✅ Exams + Marks + PDF Marksheet
- ✅ Reports (Excel export)
- ✅ Chat/Messaging (WebSocket)
- ✅ Bus GPS Tracking

### Frontend Portals:
- ✅ Public school website (school.com)
- ✅ Admin portal (/admin)
- ✅ Teacher portal (/staff)
- ✅ Student portal (/student)
- ✅ Parent portal (/parent)

### Mobile App:
- ✅ Login with biometrics
- ✅ Role-based navigation
- ✅ YouTube video player
- ✅ Attendance marking
- ✅ Push notifications (FCM)
- ✅ Bus GPS tracking
- ✅ Chat messaging

---

## 🆓 FREE TESTING DEPLOYMENT

### Step 1 — Accounts (All Free)
| Service | URL | Use |
|---|---|---|
| GitHub | github.com | Code storage |
| Railway | railway.app | Backend hosting |
| Supabase | supabase.com | PostgreSQL database |
| Vercel | vercel.com | Frontend hosting |
| Redis Cloud | redis.io/try-free | Cache + sessions |
| Firebase | console.firebase.google.com | Push notifications |

### Step 2 — Push code to GitHub
```bash
cd school-saas
git init
git add .
git commit -m "SchoolSaaS v5.0 — Complete Platform"
git remote add origin https://github.com/YOUR_USERNAME/school-saas.git
git branch -M main
git push -u origin main
```

### Step 3 — Supabase Database
1. supabase.com → New Project → Region: Mumbai
2. Settings → Database → Copy URI
3. Format needed:
   ```
   postgresql+asyncpg://postgres:PASS@db.XXXX.supabase.co:5432/postgres
   ```

### Step 4 — Generate RSA Keys (Run once locally)
```bash
cd school-saas/backend
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### Step 5 — Railway Backend Deploy
1. railway.app → New Project → GitHub → school-saas → backend folder
2. Add Environment Variables:
```
DATABASE_URL          = postgresql+asyncpg://postgres:PASS@db.XXXX.supabase.co:5432/postgres
DATABASE_URL_SYNC     = postgresql://postgres:PASS@db.XXXX.supabase.co:5432/postgres
REDIS_URL             = redis://default:PASS@redis-xxx.redis.cloud:6379
SECRET_KEY            = [run: python -c "import secrets; print(secrets.token_hex(32))"]
APP_ENV               = production
FRONTEND_URL          = https://your-app.vercel.app
ALLOWED_ORIGINS       = https://your-app.vercel.app
JWT_PRIVATE_KEY_PATH  = ./keys/private.pem
JWT_PUBLIC_KEY_PATH   = ./keys/public.pem
RAZORPAY_KEY_ID       = rzp_test_xxx
RAZORPAY_KEY_SECRET   = xxx
RAZORPAY_WEBHOOK_SECRET = xxx
```
3. Railway URL will be: `https://school-saas-production.railway.app`

### Step 6 — Vercel Frontend Deploy
1. vercel.com → New → GitHub → school-saas → **Root Directory: frontend**
2. Environment Variables:
```
VITE_API_URL     = https://school-saas-production.railway.app/api
VITE_WS_URL      = wss://school-saas-production.railway.app
VITE_RAZORPAY_KEY_ID = rzp_test_xxx
```
3. Vercel URL: `https://school-saas-xxx.vercel.app`

### Step 7 — Run DB Migrations
```bash
cd school-saas/backend
pip install -r requirements.txt
cp .env.example .env   # Fill with Supabase URL
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head
```
Or Railway runs `alembic upgrade head` automatically on deploy.

### Step 8 — Create First School + Admin (Supabase SQL Editor)
```sql
-- 1. Create school
INSERT INTO schools (id, name, code, email, phone)
VALUES (
  gen_random_uuid(), 'My School Name', 'SCH001',
  'admin@school.com', '9876543210'
) RETURNING id;

-- 2. Create admin (password: Admin@1234)
-- Copy school ID from above result
INSERT INTO users (id, school_id, full_name, email, password_hash, role, is_active, is_email_verified)
VALUES (
  gen_random_uuid(),
  'PASTE-SCHOOL-ID-HERE',
  'School Admin',
  'admin@school.com',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY.5mL4Yl7AFMEO',
  'admin', true, true
);

-- 3. Create academic year
INSERT INTO academic_years (id, school_id, year_label, start_date, end_date, is_current)
VALUES (
  gen_random_uuid(),
  'PASTE-SCHOOL-ID-HERE',
  '2024-2025',
  '2024-04-01',
  '2025-03-31',
  true
);
```

### Step 9 — Test
- Public website: `https://school-saas-xxx.vercel.app/`
- Admin login: `https://school-saas-xxx.vercel.app/login`
  - Email: `admin@school.com`
  - Password: `Admin@1234`
- API docs: `https://school-saas-production.railway.app/api/docs`

---

## 🌐 CUSTOM DOMAIN (Production)

### Option A — Cheap Domain (Recommended)
1. Buy domain from Namecheap/GoDaddy (~₹500/year): `schoolname.com`
2. Vercel → Settings → Domains → Add `schoolname.com`
3. Namecheap DNS → Add CNAME: `@ → cname.vercel-dns.com`
4. HTTPS auto-configured by Vercel ✅

### Option B — Subdomains (If you already have a domain)
```
school.com     → Vercel (React public website)
admin.school.com → Vercel (Admin portal redirect)
api.school.com → Railway (Backend)
```

Configure in Vercel → Domains → Add each subdomain.

---

## 📱 FLUTTER APP — BUILD & PUBLISH

### Android APK (Testing)
```bash
cd school-saas/mobile
flutter pub get

# Edit lib/services/api_service.dart
# Change: defaultValue: 'https://school-saas-production.railway.app/api'

flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
# Share APK directly with testers
```

### Android (Google Play Store)
```bash
# Generate keystore (once)
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload

# Build App Bundle
flutter build appbundle --release
# Upload: build/app/outputs/bundle/release/app-release.aab
# Google Play Console: $25 one-time fee
```

### iOS (App Store)
```bash
# Requires Mac + Xcode + Apple Developer ($99/year)
flutter build ios --release
# Open ios/Runner.xcworkspace in Xcode
# Archive → Upload to App Store Connect
```

### Firebase Setup (Push Notifications)
1. console.firebase.google.com → Create Project
2. Add Android App: package name `com.schoolsaas.app`
3. Download `google-services.json` → place in `mobile/android/app/`
4. Add iOS App → Download `GoogleService-Info.plist` → `mobile/ios/Runner/`
5. Backend: Set `FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json`

---

## 💰 MONETIZATION (SaaS Model)

### Pricing Plans
| Plan | Price | Features |
|---|---|---|
| **Free Trial** | ₹0 / 30 days | All features, 100 students |
| **Basic** | ₹2,999/mo | 500 students, Web only |
| **Standard** | ₹5,999/mo | 2000 students, App + Web |
| **Premium** | ₹9,999/mo | Unlimited, Video LMS, GPS |
| **Enterprise** | Custom | White-label, Custom domain |

### Payment Collection
- Accept payments via Razorpay or Instamojo
- Auto-expire access when subscription ends
- 15-day free trial for new schools

### Target Market
- Private schools (5,000+ in India)
- Coaching institutes
- Tutorial centers
- Starting price ₹2,999/mo = ₹35,988/year per school

### Revenue Projection
| Schools | Monthly Revenue |
|---|---|
| 10 | ₹50,000 |
| 50 | ₹2,50,000 |
| 100 | ₹5,00,000 |
| 500 | ₹25,00,000 |

---

## 🔐 PRODUCTION SECURITY CHECKLIST

```
Backend:
  ✅ APP_ENV=production (disables /api/docs)
  ✅ JWT RS256 (asymmetric, private key never exposed)
  ✅ bcrypt cost=12 (brute force resistant)
  ✅ Rate limiting (100 req/min per IP)
  ✅ CORS whitelist (only your domains)
  ✅ HSTS header (HTTPS enforced)
  ✅ Audit log (every action logged)
  ✅ Multi-tenant isolation (school_id on every query)

Frontend:
  ✅ Token in memory (never localStorage)
  ✅ HttpOnly cookie for refresh token
  ✅ CSP headers (via vercel.json)
  ✅ X-Frame-Options: DENY

Database:
  ✅ Supabase managed (auto-backup daily)
  ✅ SSL connection required
  ✅ Strong password

Mobile:
  ✅ Tokens in iOS Keychain / Android Keystore
  ✅ Biometric authentication
  ✅ Certificate pinning (add in production)
  ✅ No tokens in SharedPreferences
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---|---|
| Railway deploy fails | Check Build logs → usually missing env var |
| `alembic upgrade` fails | Check DATABASE_URL has `+asyncpg` or `+psycopg2` correctly |
| CORS error in browser | Update ALLOWED_ORIGINS in Railway env vars |
| Login returns 401 | Verify JWT key paths, check keys/ folder |
| Video not loading | Check YouTube URL format, ensure video is unlisted not private |
| PDF download fails | `pip install reportlab` in requirements.txt |
| Excel export fails | `pip install openpyxl` in requirements.txt |
| Flutter build fails | Run `flutter pub get`, check dart SDK version |
| FCM not working | Check google-services.json placement |

---

## 📞 SUPPORT

All 5 modules are complete. Each module builds on the previous:
- Module 1 → Foundation (Auth + DB)
- Module 2 → Core operations (Students, Staff, Attendance)
- Module 3 → Media + Payments (Videos, Fees)
- Module 4 → Academics + Mobile (Exams, Flutter App)
- Module 5 → Analytics + Communication (Reports, Chat, Bus, Public Website)

To add more features, follow the same pattern:
1. Create route file in `backend/app/api/routes/`
2. Register in `backend/app/main.py`
3. Create page in `frontend/src/pages/`
4. Add to appropriate dashboard's `<Routes>`
