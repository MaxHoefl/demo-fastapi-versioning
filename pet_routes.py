import uuid
from typing import List, Dict, Any, Optional
from fastapi import Depends, HTTPException, Request, status

from versioning_models import ApiVersion
from version_middleware import VersionedAPIRouter
from pet_repository import PetRepository, acquire_pet_repository, InMemoryPetRepository, populate_sample_data
from pet_models import (
    PetV1, PetCreateV1,
    PetV2, PetCreateV2,
    PetV3, PetCreateV3,
    PetV3_1, PetCreateV3_1
)
from pet_shims import register_pet_shims

# Create a versioned router
pet_router = VersionedAPIRouter(tags=["pets"])

# Register API shims
register_pet_shims()


# --------- Create routes with version support ---------

@pet_router.versioned_get("/pets", "1.0", "2.0", "3.0", "3.1", response_model=List[PetV3_1])
async def get_pets(
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository),
) -> List[Any]:
    """
    Get all pets.

    The actual response model will be determined based on the requested API version.
    """
    pets = await pet_repository.get_pets()
    return pets


@pet_router.versioned_get(
    "/pets/{pet_id}",
    "1.0", "2.0", "3.0", "3.1",
    response_model=PetV3_1,
    responses={404: {"description": "Pet not found"}}
)
async def get_pet(
        pet_id: uuid.UUID,
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> Any:
    """Get a pet by ID."""
    pet = await pet_repository.get_pet_by_id(pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


@pet_router.versioned_post(
    "/pets",
    "1.0", "2.0", "3.0", "3.1",
    response_model=PetV3_1,
    status_code=status.HTTP_201_CREATED
)
async def create_pet(
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> Any:
    """
    Create a new pet.

    The request body structure will be determined by the API version.
    """
    # Extract the API version from the request
    api_version = getattr(request.state, 'api_version', None)
    if not api_version:
        # Default to latest version
        api_version = ApiVersion("3.1")

    # Parse the request body according to the API version
    if str(api_version) == "1.0":
        pet_data = PetCreateV1.parse_obj(await request.json())
    elif str(api_version) == "2.0":
        pet_data = PetCreateV2.parse_obj(await request.json())
    elif str(api_version) == "3.0":
        pet_data = PetCreateV3.parse_obj(await request.json())
    else:  # 3.1 or later
        pet_data = PetCreateV3_1.parse_obj(await request.json())

    # The middleware and shims will handle conversion to latest version
    created_pet = await pet_repository.create_pet(pet_data)
    return created_pet


@pet_router.versioned_put(
    "/pets/{pet_id}",
    "1.0", "2.0", "3.0", "3.1",
    response_model=PetV3_1,
    responses={404: {"description": "Pet not found"}}
)
async def update_pet(
        pet_id: uuid.UUID,
        request: Request,
        pet_repository: PetRepository = Depends(acquire_pet_repository)
) -> Any:
    """
    Update an existing pet.

    The request body structure will be determined by the API version.
    """
    # Extract the API version from the request
    api_version = getattr(request.state, 'api_version', None)
    if not api_version:
        # Default to latest version
        api_version = ApiVersion("3.1")

    # Parse the request body according to the API version
    if str(api_version) == "1.0":
        pet_data = PetCreateV1.parse_obj(await request.json())
    elif str(api_version) == "2.0":
        pet_data = PetCreateV2.parse_obj(await request.json())
    elif str(api_version) == "3.0":
        pet_data = PetCreateV3.parse_obj(await request.json())
    else:  # 3.1 or later
        pet_data = PetCreateV3_1.parse_obj(await request.json())

    # The middleware and shims will handle conversion to latest version
    updated_pet = await pet_repository.update_pet(pet_id, pet_data)
    if not updated_pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")

    return updated_pet


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
    """Delete a pet."""
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
    # Sample data for demonstration
    shelters = {
        "1": {"id": "1", "name": "Happy Paws Shelter", "location": "New York"},
        "2": {"id": "2", "name": "Furry Friends Rescue", "location": "Los Angeles"},
        "3": {"id": "3", "name": "Whisker Haven", "location": "Chicago"}
    }

    if shelter_id not in shelters:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelter not found")

    return shelters[shelter_id]