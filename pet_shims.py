from typing import Dict, Any, List, Optional, cast
from datetime import datetime, timedelta
import copy
from versioning_models import ApiVersion, shim_registry
from pet_models import (
    PetV1, PetCreateV1,
    PetV2, PetCreateV2,
    PetV3, PetCreateV3,
    PetV3_1, PetCreateV3_1,
    PetSpeciesV1, PetSpeciesV2, PetSpeciesV3,
    PetSizeV3
)


# -------------- Request Shims (forward direction) --------------

def shim_pet_request_v1_to_v2(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a v1 pet request to v2 format."""
    # Deep copy to avoid modifying the original
    data = copy.deepcopy(request_data)

    # For POST/PUT requests with a body
    if 'body' in data and isinstance(data['body'], dict):
        # No birth_date in v1, so we estimate it from age
        if 'age' in data['body']:
            # Estimate birth date from age (years)
            age_years = data['body']['age']
            estimated_birth_date = datetime.now() - timedelta(days=age_years * 365)
            data['body']['birth_date'] = estimated_birth_date

        # Handle species mapping (all v1 species exist in v2)
        if 'species' in data['body'] and data['body']['species'] not in [s.value for s in PetSpeciesV2]:
            # Default to closest match or a default value
            data['body']['species'] = PetSpeciesV2.DOG.value

    return data


def shim_pet_request_v2_to_v3(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a v2 pet request to v3 format."""
    data = request_data

    # For POST/PUT requests with a body
    if 'body' in data and isinstance(data['body'], PetCreateV2):
        # Convert age in years to age_months
        body = data['body'].model_dump()
        if 'age' in body:
            body['age_months'] = body['age'] * 12
            del body['age']

        # Add default values for new fields
        if 'size' not in body:
            body['size'] = PetSizeV3.MEDIUM.value

        if 'tags' not in body:
            body['tags'] = []

        # Handle species mapping
        if 'species' in body and body['species'] not in [s.value for s in PetSpeciesV3]:
            # Map to closest match or default
            body['species'] = PetSpeciesV3.DOG.value

        data['body'] = PetCreateV3(**body)
    return data


def shim_pet_request_v3_to_v3_1(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a v3 pet request to v3.1 format."""
    data = request_data

    # For POST/PUT requests with a body
    if 'body' in data and isinstance(data['body'], PetCreateV3):
        body = data['body'].model_dump()
        # Add default health status if not present
        if 'health_status' not in body:
            body['health_status'] = 'good'

        data['body'] = PetCreateV3_1(**body)
    return data


# -------------- Response Shims (backward direction) --------------

def shim_pet_response_v2_to_v1(response_data: PetV2 | list[PetV2] | None) -> PetV1 | list[PetV1] | None:
    """Transform a v2 pet response to v1 format."""
    if not response_data:
        return response_data

    # Handle list responses (e.g., GET /pets)
    if isinstance(response_data, list):
        return [shim_pet_response_v2_to_v1(item) for item in response_data]

    # For response bodies
    body = response_data.model_dump()
    # Remove fields not in v1
    if 'birth_date' in body:
        del body['birth_date']

    # Ensure species is compatible with v1
    if 'species' in body and body['species'] not in [s.value for s in PetSpeciesV1]:
        # Map to closest match in v1
        body['species'] = PetSpeciesV1.DOG.value

    response_data = PetV1(**body)
    return response_data


def shim_pet_response_v3_to_v2(response_data: PetV3 | list[PetV3] | None) -> PetV2 | list[PetV2] | None:
    """Transform a v3 pet response to v2 format."""
    if not response_data:
        return response_data

    # Handle list responses
    if isinstance(response_data, list):
        return [shim_pet_response_v3_to_v2(item) for item in response_data]

    # For response bodies
    body = response_data.model_dump()
    # Convert age_months back to age in years (rounded)
    if 'age_months' in body:
        body['age'] = body['age_months'] // 12
        del body['age_months']

    # Remove fields not in v2
    if 'size' in body:
        del body['size']

    if 'tags' in body:
        del body['tags']

    # Ensure species is compatible with v2
    if 'species' in body and body['species'] not in [s.value for s in PetSpeciesV2]:
        # Map to closest match in v2
        body['species'] = PetSpeciesV2.DOG.value
    response_data = PetV2(**body)
    return response_data


def shim_pet_response_v3_1_to_v3(response_data: PetV3_1 | list[PetV3_1] | None) -> PetV3 | list[PetV3] | None:
    """Transform a v3.1 pet response to v3 format."""
    if not response_data:
        return response_data

    # Handle list responses
    if isinstance(response_data, list):
        return [shim_pet_response_v3_1_to_v3(item) for item in response_data]

    # For response bodies
    body = response_data.model_dump()
    # Remove health_status field introduced in v3.1
    if 'health_status' in body:
        del body['health_status']

    response_data = PetV3(**body)
    return response_data


# -------------- Register Shims --------------

def register_pet_shims():
    """Register all pet API shims with the shim registry."""
    # Path for pet endpoints
    pets_path = "/pets"
    pet_detail_path = "/pets/{id}"

    # Version objects
    v1_0 = ApiVersion("1.0")
    v2_0 = ApiVersion("2.0")
    v3_0 = ApiVersion("3.0")
    v3_1 = ApiVersion("3.1")

    # Register request shims (forward direction)
    shim_registry.register_request_shim(pets_path, v1_0, v2_0, shim_pet_request_v1_to_v2)
    shim_registry.register_request_shim(pets_path, v2_0, v3_0, shim_pet_request_v2_to_v3)
    shim_registry.register_request_shim(pets_path, v3_0, v3_1, shim_pet_request_v3_to_v3_1)

    shim_registry.register_request_shim(pet_detail_path, v1_0, v2_0, shim_pet_request_v1_to_v2)
    shim_registry.register_request_shim(pet_detail_path, v2_0, v3_0, shim_pet_request_v2_to_v3)
    shim_registry.register_request_shim(pet_detail_path, v3_0, v3_1, shim_pet_request_v3_to_v3_1)

    # Register response shims (backward direction)
    shim_registry.register_response_shim(pets_path, v2_0, v1_0, shim_pet_response_v2_to_v1)
    shim_registry.register_response_shim(pets_path, v3_0, v2_0, shim_pet_response_v3_to_v2)
    shim_registry.register_response_shim(pets_path, v3_1, v3_0, shim_pet_response_v3_1_to_v3)

    shim_registry.register_response_shim(pet_detail_path, v2_0, v1_0, shim_pet_response_v2_to_v1)
    shim_registry.register_response_shim(pet_detail_path, v3_0, v2_0, shim_pet_response_v3_to_v2)
    shim_registry.register_response_shim(pet_detail_path, v3_1, v3_0, shim_pet_response_v3_1_to_v3)