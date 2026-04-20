# Abroad University Study Comparison - Quick Start Guide

## Project Overview

A full-stack web application for comparing universities worldwide. Students can search, filter, compare universities, view entry requirements, and manage their academic profiles.

**Tech Stack:**
- **Frontend**: Vue 3 + Vite + Ant Design Vue
- **Backend**: FastAPI (Python)
- **Database**: MySQL
- **Authentication**: JWT tokens

---

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- Git

### 1. Clone & Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn pydantic mysql-connector-python python-dotenv pika python-jose cryptography

# Create .env file
# Copy backend/.env and fill in database credentials
cp .env.example .env

# Update config in backend/app/config.py with your database details

# Run migrations (if needed)
cd backend/migrations
python run_migration.py
cd ../..

# Start backend server
cd backend
python run.py

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 2. Setup Frontend

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

### 3. Access the Application

1. Open http://localhost:5173 in your browser
2. Click "Sign Up" to create an account
3. Fill in registration details
4. Log in with your credentials
5. Start comparing universities!

---

## 📁 Project Structure

```
Abroad-University-Study-Comparison/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                  # Main FastAPI app
│   │   ├── config.py                # Configuration
│   │   ├── database.py              # Database connection
│   │   ├── dependencies.py          # Auth dependencies
│   │   ├── routers/                 # API endpoints
│   │   │   ├── auth.py             # Auth endpoints
│   │   │   ├── users.py            # User endpoints
│   │   │   ├── universities.py      # University endpoints
│   │   │   ├── countries.py         # Country endpoints
│   │   │   └── study_bg.py          # Study background endpoints
│   │   ├── models/                  # Data models
│   │   ├── schemas/                 # Pydantic schemas
│   │   └── utils/
│   │       ├── auth.py             # JWT utilities
│   │       └── security.py         # Password hashing
│   ├── run.py                       # Startup script
│   └── .env                         # Environment variables
│
├── frontend/                         # Vue 3 frontend
│   ├── src/
│   │   ├── views/                   # Page components
│   │   │   ├── Home.vue            # Landing page
│   │   │   ├── Login.vue           # Login page
│   │   │   ├── Signup.vue          # Registration page
│   │   │   ├── Dashboard.vue       # Main layout
│   │   │   ├── Universities.vue    # Universities listing
│   │   │   ├── UniversityDetail.vue# University details
│   │   │   ├── Comparison.vue      # Comparison tool
│   │   │   └── Profile.vue         # User profile
│   │   ├── services/
│   │   │   └── api.js              # API client
│   │   ├── stores/
│   │   │   └── auth.js             # Pinia auth store
│   │   ├── router/
│   │   │   └── index.js            # Router config
│   │   ├── App.vue                 # Root component
│   │   └── main.js                 # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
│
└── README.md
```

---

## 🔐 Authentication Flow

1. **Register**: User signs up with email and password
2. **Login**: User receives access and refresh tokens
3. **Requests**: All API calls include JWT token in headers
4. **Token Expiry**: Automatic token refresh when expired
5. **Logout**: Token is invalidated on backend

---

## 📊 Main Features

### 1. University Discovery
- ✅ Search by name
- ✅ Filter by country, region, ranking
- ✅ View all 100+ universities
- ✅ See university ratings and scores

### 2. University Details
- ✅ Basic info (location, ranking, logo)
- ✅ Financial info (fees, scholarships)
- ✅ Student demographics (total, international, domestic)
- ✅ Entry requirements (Bachelor/Master)
- ✅ Academic scores by category

### 3. Comparison Tool
- ✅ Compare up to 5 universities
- ✅ Side-by-side comparison table
- ✅ Entry requirements chart
- ✅ Scholarship & admission comparison

### 4. User Management
- ✅ Profile management
- ✅ Password change
- ✅ Study background tracking
- ✅ Personal information storage

---

## 📝 API Endpoints Reference

### Authentication
```
POST   /api/auth/signup           - Register new user
POST   /api/auth/login            - Login user
POST   /api/auth/refresh          - Refresh access token
POST   /api/auth/logout           - Logout user
```

### Users
```
GET    /api/users/me              - Get current user
PUT    /api/users/me              - Update profile
PUT    /api/users/me/password     - Change password
GET    /api/users/{id}            - Get user by ID
```

### Universities
```
GET    /api/universities          - List universities
GET    /api/universities/{id}     - Get university detail
GET    /api/universities/search?q=query     - Search
GET    /api/universities/filter   - Filter by criteria
GET    /api/universities/{id}/entry-requirements - Entry reqs
POST   /api/universities/compare  - Compare universities
POST   /api/universities/chart-data - Get chart data
```

### Other
```
GET    /api/countries             - Get all countries
GET    /api/study-bg              - Get study background
PUT    /api/study-bg              - Update study background
```

---

## 🛠 Common Tasks

### Add New University Data
1. Prepare CSV file with university data
2. Run migration script: `python backend/migrations/run_migration.py`
3. Data is inserted into MySQL database

### Modify Authentication
Edit `backend/app/config.py`:
```python
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### Change API URL
Edit `frontend/src/services/api.js`:
```javascript
const API_BASE_URL = 'http://your-backend-url/api'
```

### Build for Production

**Frontend:**
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

**Backend:**
```bash
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

---

## 🔍 Testing

### Test Backend API
Visit http://localhost:8000/docs for interactive API documentation

### Test Frontend
1. Sign up with test email
2. Search for universities
3. Add to comparison
4. Update profile
5. Change password

---

## ⚠️ Troubleshooting

### Backend won't start
- Check MySQL is running
- Verify database credentials in `.env`
- Check Python version (3.11+)

### Frontend won't load
- Clear browser cache
- Check backend is running
- Verify API URL in `src/services/api.js`

### CORS errors
- Backend has CORS enabled for `http://localhost:5173`
- If deploying, update in `backend/app/main.py`:
```python
allow_origins=["http://your-domain.com"]
```

### Login fails
- Check database has users table
- Verify database migrations ran
- Check email/password are correct

---

## 📱 Responsive Design

The application is fully responsive:
- **Mobile**: 320px+ (optimized for small screens)
- **Tablet**: 768px+ (two-column layouts)
- **Desktop**: 1200px+ (full features)

---

## 🚀 Deployment

### Frontend (Netlify/Vercel)
```bash
npm run build
# Deploy dist/ folder
```

### Backend (Heroku/Railway/Replit)
```bash
# Create Procfile:
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT app.main:app" > Procfile
```

---

## 📚 Documentation

- **Frontend Setup**: `frontend/SETUP.md`
- **Backend Docs**: `backend/README.md` (if available)
- **API Docs**: http://localhost:8000/docs

---

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit pull request

---

## 📄 License

[Your License Here]

---

## 📧 Support

For questions or issues:
- Check existing documentation
- Review error messages carefully
- File an issue with details

---

**Last Updated**: 2026
**Version**: 1.0.0
