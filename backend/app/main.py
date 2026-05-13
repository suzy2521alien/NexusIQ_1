from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as evidence_router

app = FastAPI(
    title="Digital Evidence Intelligence System",
    description="Multi-layered architecture for digital evidence ingestion and intelligence extraction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evidence_router)


@app.get("/")
async def root():
    return {
        "message": "Digital Evidence Intelligence System API",
        "version": "1.0.0",
        "module": "Data Ingestion & Basic Intelligence Extraction"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "module": "active"}
