"""
Gestantes Service - FastAPI entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.fhir.router import router as fhir_router
from app.routers import consentimentos, gestantes

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Gestantes Service API with FHIR R4 support",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gestantes.router, prefix="/api/v1")
app.include_router(consentimentos.router, prefix="/api/v1")
app.include_router(fhir_router)


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "fhir": "/fhir/metadata",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

