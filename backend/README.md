# Backend API - University Comparison

FastAPI backend for University Comparison Web Application.

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: MySQL 8.x
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt
- **Python**: 3.9+

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── dependencies.py      # Dependency injection (will be created)
│   ├── models/              # Data access layer
│   ├── schemas/             # Pydantic models (to be created)
│   ├── routers/             # API routes (to be created)
│   └── utils/               # Utilities (auth, security) (to be created)
├── migrations/              # SQL migration files
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (DO NOT commit)
└── .env.example             # Example environment file
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Or using virtual environment:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
# Edit .env with your configurations
```

**Important**: Change `SECRET_KEY` to a random 32-character hex string:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Database Setup

Make sure MySQL is running and create the database:

```sql
CREATE DATABASE universities_db_clone CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run the migration to create `refresh_tokens` table:

```bash
mysql -u user -p universities_db_clone < migrations/001_create_refresh_tokens_table.sql
```

### 4. Run Development Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
python -m app.main
```

### 5. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Development Status

### ✅ Completed

- [x] Project structure setup
- [x] Configuration management
- [x] Database connection
- [x] CORS middleware
- [x] Basic FastAPI app with health check
- [x] Database migration for refresh_tokens

### 🚧 In Progress

- [ ] Auth routes (signup, login, refresh, logout)
- [ ] User routes (profile, update, password change)
- [ ] University routes (list, detail, compare)
- [ ] Study background routes
- [ ] Country routes
- [ ] Admin routes

## API Endpoints (Planned)

See the full API documentation in the [Implementation Plan](../C:\Users\Asus\.claude\plans\ticklish-cooking-lemur.md)

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout and invalidate refresh token

### Users
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update profile
- `PUT /api/users/me/password` - Change password

### Universities
- `GET /api/universities` - List universities with filters
- `GET /api/universities/{id}` - Get university details
- `POST /api/universities/compare` - Compare universities
- `GET /api/universities/{id}/entry-requirements` - Get entry requirements

## Next Steps

1. **Phase 2.1**: Implement Auth & Security
   - Create utils/security.py and utils/auth.py
   - Create schemas/auth.py
   - Create routers/auth.py
   - Test authentication flow

2. **Phase 2.2**: Implement User Routes
   - Create schemas/user.py
   - Adapt models/user.py from existing UserModel.py
   - Create routers/users.py

3. **Phase 2.3**: Implement University Routes
   - Create schemas/university.py
   - Adapt models/university.py from existing UniversityModel.py
   - Create routers/universities.py

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test authentication (after implementing)
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","email":"john@example.com","password":"password123"}'
```

## Notes

- All API routes are prefixed with `/api/`
- JWT tokens are used for authentication
- CORS is enabled for frontend dev server (http://localhost:5173)
- Database uses existing `universities_db_clone` schema (no schema migration needed except refresh_tokens table)
