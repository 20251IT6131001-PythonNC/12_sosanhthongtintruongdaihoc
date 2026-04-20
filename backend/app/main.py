from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Import routers
from app.routers import auth, users, universities, study_bg, countries
# from app.routers import admin  # Will be created later

app = FastAPI(
    title="University Comparison API",
    description="REST API for university comparison web application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


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

