import uuid
from functools import cache
from typing import Dict, List, Optional, Any
from datetime import datetime

from pet_models import (
    PetRepository,
    PetV3_1 as Pet,  # We'll use the latest version internally
    PetCreateV3_1 as PetCreate
)


class InMemoryPetRepository(PetRepository):
    """
    An in-memory implementation of the PetRepository interface.
    Uses the latest model version (v3.1) internally.
    """
    def __init__(self):
        self._pets: Dict[uuid.UUID, Pet] = {}

    async def get_pets(self) -> List[Pet]:
        """Get all pets."""
        return list(self._pets.values())

    async def get_pet_by_id(self, pet_id: uuid.UUID) -> Optional[Pet]:
        """Get a pet by ID."""
        return self._pets.get(pet_id)

    async def create_pet(self, pet_data: PetCreate) -> Pet:
        """Create a new pet."""
        pet_id = uuid.uuid4()

        # Create a new pet using the latest model version
        pet = Pet(
            id=pet_id,
            **pet_data.dict()
        )

        # Store the pet
        self._pets[pet_id] = pet
        return pet

    async def update_pet(self, pet_id: uuid.UUID, pet_data: PetCreate) -> Optional[Pet]:
        """Update an existing pet."""
        if pet_id not in self._pets:
            return None

        # Update the pet with new data
        updated_pet = Pet(
            id=pet_id,
            **pet_data.dict()
        )

        self._pets[pet_id] = updated_pet
        return updated_pet

    async def delete_pet(self, pet_id: uuid.UUID) -> bool:
        """Delete a pet."""
        if pet_id not in self._pets:
            return False

        del self._pets[pet_id]
        return True


@cache
def acquire_pet_repository() -> PetRepository:
    return InMemoryPetRepository()


async def populate_sample_data(repository: InMemoryPetRepository):
    sample_pets = [
        {
            "name": "Buddy",
            "species": "dog",
            "age_months": 24,
            "birth_date": datetime(2023, 5, 15),
            "size": "medium",
            "tags": ["friendly", "trained"],
            "health_status": "excellent"
        },
        {
            "name": "Whiskers",
            "species": "cat",
            "age_months": 36,
            "birth_date": datetime(2022, 5, 10),
            "size": "small",
            "tags": ["indoor", "playful"],
            "health_status": "good"
        },
        {
            "name": "Rex",
            "species": "dog",
            "age_months": 48,
            "birth_date": datetime(2021, 5, 10),
            "size": "large",
            "tags": ["guard dog", "trained"],
            "health_status": "good"
        }
    ]

    # Add each pet to the repository
    for pet_data in sample_pets:
        await repository.create_pet(PetCreate(**pet_data))