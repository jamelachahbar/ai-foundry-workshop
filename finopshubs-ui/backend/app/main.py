from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
import uvicorn
from app.routers import finops

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FinOps Hubs UI API",
    description="API for FinOps Hubs UI",
    version="0.1.0",
)

# Configure CORS
origins = [
    "http://localhost:3000",   # Frontend on port 3000
    "http://127.0.0.1:3000",   # Alternate localhost
    "http://localhost:5173",   # Vite default port
    "http://127.0.0.1:5173",   # Alternate Vite
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(finops.router)

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Welcome to FinOps Hubs UI API"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred"},
    )

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True) 