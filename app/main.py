from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.routes import auth
from app.config import settings

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistem Monitoring Infrastruktur Jalan",
    description="Dashboard untuk memonitoring kondisi infrastruktur jalan",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.get("/api/")
def root():
    return {
        "status": "success",
        "code": 200,
        "message": "Sistem Monitoring Infrastruktur Jalan API",
        "data": {
            "version": "1.0.0",
            "docs": "/docs"
        }
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "success",
        "code": 200,
        "message": "Service is healthy",
        "data": {
            "status": "healthy"
        }
    }

from mangum import Mangum
handler = Mangum(app)

# Local development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=settings.DEBUG)