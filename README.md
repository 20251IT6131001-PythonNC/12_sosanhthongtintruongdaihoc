# University Comparison - Web Application

Hệ thống so sánh các trường đại học quốc tế được chuyển đổi từ Desktop App (tkinter) sang Web App (Vue.js + FastAPI).

## 📋 Tổng quan

Dự án migrate từ Python Tkinter Desktop Application sang Modern Web Application với:
- **Frontend**: Vue.js 3 + Ant Design Vue + Pinia
- **Backend API**: FastAPI + MySQL
- **Authentication**: JWT (JSON Web Tokens)

## 🏗️ Kiến trúc

```
Abroad-University-Study-Comparison/
├── backend/              # FastAPI REST API
│   ├── app/
│   │   ├── main.py      # API entry point
│   │   ├── config.py    # Configuration
│   │   ├── database.py  # DB connection
│   │   ├── models/      # Data access layer
│   │   ├── schemas/     # Pydantic models (to be created)
│   │   ├── routers/     # API routes (to be created)
│   │   └── utils/       # Auth & security (to be created)
│   ├── migrations/      # SQL migrations
│   └── requirements.txt
│
├── frontend/            # Vue.js 3 SPA
│   ├── src/
│   │   ├── main.js      # Vue entry point
│   │   ├── router/      # Vue Router
│   │   ├── stores/      # Pinia stores (to be created)
│   │   ├── api/         # API clients (to be created)
│   │   ├── components/  # Reusable components (to be created)
│   │   ├── views/       # Page components
│   │   └── layouts/     # Layout components (to be created)
│   └── package.json
│
├── models/              # Existing Python models (will be adapted)
├── controller/          # Existing controllers (reference)
├── ui/                  # Existing tkinter UI (reference)
├── data/                # Data scripts and datasets
└── assets/              # Static assets (will be copied to frontend)
```

## 🚀 Quick Start

### Prerequisites

- **Python**: 3.9+ (for backend)
- **Node.js**: 20.19+ or 22.12+ (for frontend) - *Note: older versions may work with `--legacy-peer-deps`*
- **MySQL**: 8.0+
- **Git**: For version control

### 1. Clone Repository

```bash
git clone <repository-url>
cd Abroad-University-Study-Comparison
```

### 2. Database Setup

Ensure MySQL is running and the database exists:

```sql
CREATE DATABASE universities_db_clone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migration for refresh_tokens table:

```bash
mysql -u user -p universities_db_clone < backend/migrations/001_create_refresh_tokens_table.sql
```

### 3. Backend Setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (.env already created with default values)
# Optionally update DATABASE_PASSWORD in .env

# Run development server
uvicorn app.main:app --reload
```

Backend will be available at: **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# If you get version errors, try: npm install --legacy-peer-deps

# Run development server
npm run dev
```

Frontend will be available at: **http://localhost:5173**

## 📚 Documentation

- [Backend README](./backend/README.md) - Detailed backend documentation
- [Frontend README](./frontend/README.md) - Detailed frontend documentation
- [Implementation Plan](./C:\Users\Asus\.claude\plans\ticklish-cooking-lemur.md) - Full migration plan

## 🎯 Development Status

### Phase 1: Setup & Infrastructure ✅ COMPLETED

- [x] Backend structure with FastAPI
- [x] Frontend structure with Vue.js + Vite
- [x] Configuration files (.env, vite.config.js, etc.)
- [x] Database migration (refresh_tokens table)
- [x] Basic FastAPI app with CORS
- [x] Basic Vue app with Ant Design Vue
- [x] READMEs and documentation

### Phase 2: Backend API Development 🚧 IN PROGRESS

**Priority 1: Auth & Security**
- [ ] Create utils/security.py (password hashing)
- [ ] Create utils/auth.py (JWT tokens)
- [ ] Create schemas/auth.py (Pydantic models)
- [ ] Create routers/auth.py (signup, login, refresh, logout)
- [ ] Create dependencies.py (get_current_user, get_current_admin)

**Priority 2-5**: User routes, University routes, Study background, Admin routes...

### Phase 3: Frontend Core Development 🔜 PLANNED

- [ ] API client setup (axios with interceptors)
- [ ] Auth store (Pinia)
- [ ] SignIn/SignUp pages
- [ ] Router guards for authentication
- [ ] Header, Footer, Layouts

### Phase 4-7: Features, Testing, Deployment 🔜 PLANNED

See [Implementation Plan](./C:\Users\Asus\.claude\plans\ticklish-cooking-lemur.md) for details.

## 🔑 Key Features (from Tkinter app)

- ✅ User authentication (signup, login)
- ✅ University search and filtering
- ✅ University detail pages with entry requirements
- ✅ Compare multiple universities (up to 5)
- ✅ User profile management
- ✅ Study background tracking
- ✅ Admin panel for CRUD operations
- ❌ Chatbot (temporarily skipped)

## 🛠️ Tech Stack

### Backend
- FastAPI 0.109.0
- MySQL 8.x
- JWT Authentication
- bcrypt password hashing
- Pydantic for validation

### Frontend
- Vue.js 3.4 (Composition API)
- Ant Design Vue 4.x
- Pinia (state management)
- Vue Router 4
- Axios (HTTP client)
- Chart.js (for charts)
- Vite 5 (build tool)

## 📝 API Endpoints (Planned)

### Authentication
- `POST /api/auth/signup` - Register
- `POST /api/auth/login` - Login with JWT
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Invalidate refresh token

### Universities
- `GET /api/universities` - List with filters & pagination
- `GET /api/universities/{id}` - Get details
- `POST /api/universities/compare` - Compare multiple

### Users & Profile
- `GET /api/users/me` - Current user profile
- `PUT /api/users/me` - Update profile
- `PUT /api/users/me/password` - Change password
- `GET /api/study-bg/me` - Study background
- `PUT /api/study-bg/me` - Update study background

### Admin (Protected)
- User CRUD, University CRUD

See full API spec in Implementation Plan.

## 🧪 Testing

### Backend
```bash
# Health check
curl http://localhost:8000/health

# After auth implementation
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@example.com","password":"password123"}'
```

### Frontend
```bash
# Run dev server and open http://localhost:5173
cd frontend && npm run dev
```

## 📦 Deployment (Future)

### Backend
- Options: Railway, Render, Fly.io, AWS EC2
- Requires: MySQL database (RDS, managed MySQL)

### Frontend
- Options: Vercel, Netlify (recommended)
- Build: `npm run build` → deploy `dist/` folder

## 🤝 Contributing

This is a migration project from desktop to web. Follow the Implementation Plan for development order.

## 📄 License

[Add your license here]

## 👥 Team

[Add team members here]

---

**Current Milestone**: Phase 1 Complete ✅ - Phase 2 Starting 🚀

For detailed development workflow, see the [Implementation Plan](./C:\Users\Asus\.claude\plans\ticklish-cooking-lemur.md).
