# How to Run the FastAPI Server

## Quick Start (Recommended)

### Option 1: Using the startup script (easiest)
```bash
cd backend
python run.py
```

### Option 2: Using uvicorn directly (also good)
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using uvicorn command (if installed globally)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Access the API

Once the server is running, you can access:

- **API Root**: http://localhost:8000/
- **Swagger UI (Interactive Docs)**: http://localhost:8000/docs
- **ReDoc (Alternative Docs)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## Common Issues & Solutions

### Issue: "Cannot find module 'app'"
**Solution**: Make sure you're running from the `backend` directory
```bash
cd backend
python -m uvicorn app.main:app --reload
```

### Issue: "Port 8000 already in use"
**Solution**: Use a different port
```bash
python -m uvicorn app.main:app --reload --port 8001
```

### Issue: "ModuleNotFoundError" or "No module named 'uvicorn'"
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Database connection errors
**Solution**: Check your `.env` file in the backend directory
```bash
# Make sure these are set correctly:
DATABASE_HOST=localhost
DATABASE_USER=root
DATABASE_PASSWORD=your_password
DATABASE_NAME=universities_db_clone
SECRET_KEY=your_secret_key_here
```

---

## Environment Setup

### 1. Create virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 4. Run the server
```bash
python run.py
```

---

## Production Deployment

For production, use Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Or with more workers for higher concurrency:
```bash
gunicorn app.main:app -w 8 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Development Tips

### Disable auto-reload (for debugging)
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run with specific log level
```bash
python -m uvicorn app.main:app --log-level debug --reload
```

### Run with SSL/TLS (for HTTPS)
```bash
python -m uvicorn app.main:app --reload --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

---

## API Endpoints Overview

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/logout` - Logout

### Users
- `GET /api/users/me` - Get current user
- `PUT /api/users/me` - Update profile
- `PUT /api/users/me/password` - Change password
- `GET /api/users/{user_id}` - Get user by ID

### Universities
- `GET /api/universities/` - List universities
- `GET /api/universities/search` - Search
- `GET /api/universities/filter` - Filter
- `GET /api/universities/{id}` - Get details
- `GET /api/universities/{id}/entry-requirements` - Entry requirements
- `POST /api/universities/compare` - Compare
- `POST /api/universities/chart-data` - Chart data

### Study Background
- `GET /api/study-bg/me` - Get study background
- `POST /api/study-bg/me` - Create
- `PUT /api/study-bg/me` - Update
- `DELETE /api/study-bg/me` - Delete
- `GET /api/study-bg/{user_id}` - Get for user

### Countries
- `GET /api/countries/` - List all
- `GET /api/countries/search` - Search
- `GET /api/countries/{id}` - Get by ID

---

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# List universities
curl http://localhost:8000/api/universities/

# Search universities
curl "http://localhost:8000/api/universities/search?q=MIT"
```

### Using Python
```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# List universities
response = requests.get("http://localhost:8000/api/universities/")
print(response.json())
```

### Using the Swagger UI
Just navigate to http://localhost:8000/docs and try the endpoints interactively!

---

## Monitoring & Logs

The server logs requests to the console. Look for:
- `INFO` - Normal operations
- `WARNING` - Potential issues
- `ERROR` - Errors that occurred

For more detailed logs, use:
```bash
python -m uvicorn app.main:app --log-level debug --reload
```

---

## Troubleshooting

If you encounter issues:

1. **Check logs** - Look at the console output for error messages
2. **Verify database** - Make sure MySQL is running and `.env` is correct
3. **Test health endpoint** - `curl http://localhost:8000/health`
4. **Check Swagger docs** - Go to http://localhost:8000/docs
5. **Look at error responses** - They include detailed error messages

For more help, check the main README.md file in the backend directory.
