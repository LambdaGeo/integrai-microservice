"""
Users Service - FastAPI Main Application
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import get_password_hash
from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import audit, auth, usuarios
from app.fhir.router import router as fhir_router

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Users Service API with FHIR R4 support",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(fhir_router)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    # Import all models to register them with Base
    from app.models.usuario import AgenteProfile, AuditLog, Usuario
    
    # Create tables (only for development - use Alembic in production)
    Base.metadata.create_all(bind=engine)

    username = (
        os.environ.get("DJANGO_SUPERUSER_USERNAME")
        or os.environ.get("DJANGO_SUPERUSER_CPF")
        or os.environ.get("USERS_SUPERUSER_USERNAME")
    )
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL") or os.environ.get("USERS_SUPERUSER_EMAIL")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD") or os.environ.get("USERS_SUPERUSER_PASSWORD")
    profile_name = os.environ.get("DJANGO_SUPERUSER_NAME") or os.environ.get("USERS_SUPERUSER_NAME") or "Administrador"

    if not username or not password:
        print("Superuser seed skipped: username or password not configured.")
        return

    username = "".join(filter(str.isdigit, username))
    if not username:
        print("Superuser seed skipped: username must contain digits.")
        return

    db = SessionLocal()
    try:
        user = db.query(Usuario).filter(Usuario.username == username).first()
        if user:
            changed = False
            promote_to_superuser = not user.is_staff or not user.is_superuser
            if promote_to_superuser:
                user.hashed_password = get_password_hash(password)
                changed = True
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_superuser:
                user.is_superuser = True
                changed = True
            if email and user.email != email:
                user.email = email
                changed = True
            if changed:
                db.commit()
                print("Existing superuser updated.")
            else:
                print("Superuser already exists.")
        else:
            user = Usuario(
                username=username,
                email=email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_staff=True,
                is_superuser=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("Superuser created.")

        profile = db.query(AgenteProfile).filter(AgenteProfile.user_id == user.id).first()
        if not profile:
            db.add(AgenteProfile(user_id=user.id, nome=profile_name))
            db.commit()
            print("Superuser profile created.")
    finally:
        db.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "fhir": "/fhir/metadata"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
