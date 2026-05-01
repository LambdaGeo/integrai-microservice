"""
Users Service - FastAPI Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, usuarios
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
app.include_router(fhir_router)


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup"""
    # Import all models to register them with Base
    from app.models.usuario import Usuario, AgenteProfile
    
    # Create tables (only for development - use Alembic in production)
    Base.metadata.create_all(bind=engine)


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
