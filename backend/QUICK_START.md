# FastAPI Server - Quick Reference

## Start the Server

Choose ONE of these commands (from `backend` directory):

### ⭐ Recommended (easiest)
```bash
python run.py
```

### Alternative 1
```bash
python -m uvicorn app.main:app --reload
```

### Alternative 2
```bash
python -m app
```

---

## Access the API

Once running, open in your browser:

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | API root info |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/redoc | Alternative docs (ReDoc) |
| http://localhost:8000/health | Health check |

---

## Common Workflows

### 1. First Time Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
python run.py
```

### 2. Daily Development
```bash
cd backend
python run.py
# Code changes auto-reload
```

### 3. Test an Endpoint
```bash
# In your browser or another terminal:
curl http://localhost:8000/health
curl http://localhost:8000/api/universities/
```

### 4. Stop the Server
```bash
Press CTRL+C in the terminal
```

---

## Configuration

Edit these files if needed:

- **`.env`** - Database credentials & secrets
- **`app/config.py`** - Application settings
- **`app/database.py`** - Database connection

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Port 8000 in use" | `python -m uvicorn app.main:app --port 8001` |
| "Cannot find module 'app'" | Make sure you're in `backend` directory |
| "Database connection error" | Check `.env` file settings |
| "Module not found" | Run `pip install -r requirements.txt` |

---

## API Structure

```
/api/
├── /auth/       - Login, signup, tokens
├── /users/      - User profile & settings
├── /universities/ - University data
├── /study-bg/   - Study background info
└── /countries/  - Country list
```

Total endpoints: **23 API operations**

---

## Documentation Files

- `README.md` - Full documentation
- `STARTUP_GUIDE.md` - Detailed startup instructions
- `MIGRATION_GUIDE.md` - Backend migration details

---

## Need Help?

1. Check the Swagger UI: http://localhost:8000/docs
2. Read STARTUP_GUIDE.md for detailed instructions
3. Check console logs for error messages
4. Verify database connection in `.env`

---

Good to go! 🚀
