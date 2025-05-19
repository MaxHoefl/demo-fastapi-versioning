from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from version_middleware import VersionNegotiationMiddleware
from pet_routes import pet_router
from pet_repository import InMemoryPetRepository, populate_sample_data

app = FastAPI(
    title="Pet Store API",
    description="A versioned REST API for managing pets",
    version="3.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(VersionNegotiationMiddleware)

app.include_router(pet_router, prefix="")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


@app.on_event("startup")
async def startup_event():
    repository = InMemoryPetRepository()
    await populate_sample_data(repository)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)