import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------- API v1.0 Models ----------------
class PetSpeciesV1(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"


class PetV1(BaseModel):
    id: uuid.UUID
    name: str
    species: PetSpeciesV1
    age: int  # Age in years

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fluffy",
                "species": "dog",
                "age": 3
            }
        }


class PetCreateV1(BaseModel):
    name: str
    species: PetSpeciesV1
    age: int

    class Config:
        schema_extra = {
            "example": {
                "name": "Fluffy",
                "species": "dog",
                "age": 3
            }
        }


# ---------------- API v2.0 Models ----------------
class PetSpeciesV2(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    FISH = "fish"  # Added a new species option
    REPTILE = "reptile"  # Added a new species option


class PetV2(BaseModel):
    id: uuid.UUID
    name: str
    species: PetSpeciesV2
    age: int  # Age in years
    birth_date: Optional[datetime] = None  # Added birth date field

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fluffy",
                "species": "dog",
                "age": 3,
                "birth_date": "2020-01-01T00:00:00Z"
            }
        }


class PetCreateV2(BaseModel):
    name: str
    species: PetSpeciesV2
    age: int
    birth_date: Optional[datetime] = None

    class Config:
        schema_extra = {
            "example": {
                "name": "Fluffy",
                "species": "dog",
                "age": 3,
                "birth_date": "2020-01-01T00:00:00Z"
            }
        }


# ---------------- API v3.0 Models ----------------
class PetSpeciesV3(str, Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    FISH = "fish"
    REPTILE = "reptile"
    RABBIT = "rabbit"  # Added a new species option
    HAMSTER = "hamster"  # Added a new species option


class PetSizeV3(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class PetV3(BaseModel):
    id: uuid.UUID
    name: str
    species: PetSpeciesV3
    age_months: int  # Changed from years to months for precision
    birth_date: Optional[datetime] = None
    size: PetSizeV3 = PetSizeV3.MEDIUM  # Added size field with default
    tags: List[str] = Field(default_factory=list)  # Added tags

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fluffy",
                "species": "dog",
                "age_months": 36,
                "birth_date": "2020-01-01T00:00:00Z",
                "size": "medium",
                "tags": ["friendly", "trained"]
            }
        }


class PetCreateV3(BaseModel):
    name: str
    species: PetSpeciesV3
    age_months: int
    birth_date: Optional[datetime] = None
    size: PetSizeV3 = PetSizeV3.MEDIUM
    tags: List[str] = Field(default_factory=list)

    class Config:
        schema_extra = {
            "example": {
                "name": "Fluffy",
                "species": "dog",
                "age_months": 36,
                "birth_date": "2020-01-01T00:00:00Z",
                "size": "medium",
                "tags": ["friendly", "trained"]
            }
        }


# ---------------- V3.1 API Models ----------------
# Let's say v3.1 introduces a health status field
class PetHealthStatusV3_1(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class PetV3_1(BaseModel):
    id: uuid.UUID
    name: str
    species: PetSpeciesV3
    age_months: int
    birth_date: Optional[datetime] = None
    size: PetSizeV3 = PetSizeV3.MEDIUM
    tags: List[str] = Field(default_factory=list)
    health_status: PetHealthStatusV3_1 = PetHealthStatusV3_1.GOOD  # New field in v3.1

    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Fluffy",
                "species": "dog",
                "age_months": 36,
                "birth_date": "2020-01-01T00:00:00Z",
                "size": "medium",
                "tags": ["friendly", "trained"],
                "health_status": "good"
            }
        }


class PetCreateV3_1(BaseModel):
    name: str
    species: PetSpeciesV3
    age_months: int
    birth_date: Optional[datetime] = None
    size: PetSizeV3 = PetSizeV3.MEDIUM
    tags: List[str] = Field(default_factory=list)
    health_status: PetHealthStatusV3_1 = PetHealthStatusV3_1.GOOD

    class Config:
        schema_extra = {
            "example": {
                "name": "Fluffy",
                "species": "dog",
                "age_months": 36,
                "birth_date": "2020-01-01T00:00:00Z",
                "size": "medium",
                "tags": ["friendly", "trained"],
                "health_status": "good"
            }
        }


# Repository interface definition that will be implemented
class PetRepository:
    async def get_pets(self) -> List[Any]:
        raise NotImplementedError()

    async def get_pet_by_id(self, pet_id: uuid.UUID) -> Any:
        raise NotImplementedError()

    async def create_pet(self, pet_data: Any) -> Any:
        raise NotImplementedError()

    async def update_pet(self, pet_id: uuid.UUID, pet_data: Any) -> Any:
        raise NotImplementedError()

    async def delete_pet(self, pet_id: uuid.UUID) -> bool:
        raise NotImplementedError()