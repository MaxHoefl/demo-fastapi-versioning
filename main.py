from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from version_middleware import VersionNegotiationMiddleware
from pet_routes import pet_router
from pet_repository import InMemoryPetRepository, populate_sample_data

# Create FastAPI application
app = FastAPI(
    title="Pet Store API",
    description="A versioned REST API for managing pets",
    version="3.1.0",  #   Current API version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production you should specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add version negotiation middleware
app.add_middleware(VersionNegotiationMiddleware)

# Include routers
app.include_router(pet_router, prefix="")


# Global exception handler for version negotiation errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


# Startup event to initialize data
@app.on_event("startup")
async def startup_event():
    """Initialize the application with sample data."""
    # Create a repository instance
    repository = InMemoryPetRepository()

    # Populate with sample data
    await populate_sample_data(repository)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)