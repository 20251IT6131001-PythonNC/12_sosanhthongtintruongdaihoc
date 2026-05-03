from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.utils.rate_limit import limiter
import os

# Import routers
from app.routers import auth, users, universities, study_bg, countries, chatbot, scholarships
# from app.routers import admin  # Will be created later

app = FastAPI(
    title="University Comparison API",
    description="REST API for university comparison web application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(universities.router, prefix="/api/universities", tags=["Universities"])
app.include_router(study_bg.router, prefix="/api/study-bg", tags=["Study Background"])
app.include_router(countries.router, prefix="/api/countries", tags=["Countries"])
app.include_router(chatbot.router,    prefix="/api/chatbot",    tags=["Chatbot"])
app.include_router(scholarships.router, prefix="/api/scholarships", tags=["Scholarships"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Serve static files (e.g. uploaded avatars)
_static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/")
def root():
    """Root endpoint - API info"""
    return {
        "message": "University Comparison API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

