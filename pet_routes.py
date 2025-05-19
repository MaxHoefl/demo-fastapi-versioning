import uuid
from typing import List, Dict, Any
from fastapi import Depends, HTTPException, Request, status

from version_middleware import VersionedAPIRouter
from pet_repository import PetRepository, acquire_pet_repository
from pet_models import (
    PetV1, PetCreateV1,
    PetV2, PetCreateV2,
    PetV3, PetCreateV3,
    PetV3_1, PetCreateV3_1
)
from pet_shims import register_pet_shims


pet_router = VersionedAPIRouter(tags=["pets"])

register_pet_shims()


# --------- Create routes with version support ---------

@pet_router.versioned_get(
    "/pets",
    "1.0", "2.0", "3.0", "3.1")
async def get_pets(
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository),
) -> List[PetV1 | PetV2 | PetV3 | PetV3_1]:
    """
    Get all pets.
    The actual response model will be determined based on the requested API version.
    """
    pets = await pet_repository.get_pets()
    return pets


@pet_router.versioned_get(
    "/pets/{pet_id}",
    "1.0", "2.0", "3.0", "3.1",
    responses={404: {"description": "Pet not found"}}
)
async def get_pet(
        pet_id: uuid.UUID,
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> PetV1 | PetV2 | PetV3 | PetV3_1:
    pet = await pet_repository.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


@pet_router.versioned_post(
    "/pets",
    "1.0", "2.0", "3.0", "3.1",
    status_code=status.HTTP_201_CREATED
)
async def create_pet(
        body: PetCreateV1 | PetCreateV2 | PetCreateV3 | PetCreateV3_1,
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> PetCreateV1 | PetCreateV2 | PetCreateV3 | PetCreateV3_1:
    """
    Create a new pet.
    The request body structure will be determined by the API version.
    """
    # The middleware and shims will handle conversion to latest version
    created_pet = await pet_repository.create_pet(body)
    return created_pet


@pet_router.versioned_delete(
    "/pets/{pet_id}",
    "1.0", "2.0", "3.0", "3.1",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Pet not found"}}
)
async def delete_pet(
        pet_id: uuid.UUID,
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> None:
    success = await pet_repository.delete_pet(pet_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return None


# ---------- Routes only available in newer versions ----------

# Shelter endpoints only available in v3.0 and later
@pet_router.versioned_get("/shelters", "3.0", "3.1")
async def get_shelters(request: Request) -> List[Dict[str, Any]]:
    """
    Get all pet shelters.
    This endpoint is only available in API v3.0 and later.
    """
    # Sample data for demonstration
    shelters = [
        {"id": "1", "name": "Happy Paws Shelter", "location": "New York"},
        {"id": "2", "name": "Furry Friends Rescue", "location": "Los Angeles"},
        {"id": "3", "name": "Whisker Haven", "location": "Chicago"}
    ]
    return shelters


@pet_router.versioned_get("/shelters/{shelter_id}", "3.0", "3.1")
async def get_shelter(shelter_id: str, request: Request) -> Dict[str, Any]:
    """
    Get a shelter by ID.
    This endpoint is only available in API v3.0 and later.
    """
    shelters = {
        "1": {"id": "1", "name": "Happy Paws Shelter", "location": "New York"},
        "2": {"id": "2", "name": "Furry Friends Rescue", "location": "Los Angeles"},
        "3": {"id": "3", "name": "Whisker Haven", "location": "Chicago"}
    }

    if shelter_id not in shelters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelter not found")

    return shelters[shelter_id]