# FastAPI Header-Based API Versioning Guide

This guide explains how to use the header-based API versioning system implemented for our REST API.

## Directory Structure

```
app/
├── __init__.py
├── main.py                  # FastAPI application
├── versioning_models.py     # Version and registry models
├── version_middleware.py    # Version negotiation middleware
├── pet_models.py            # Pet data models for each version
├── pet_shims.py             # Version transformation shims
├── pet_repository.py        # Repository implementation
└── pet_routes.py            # API routes
```

## How API Versioning Works

### Version Negotiation

1. **Discovering Supported Versions**:
   Send a HEAD request to any endpoint to discover which API versions are supported.
   ```bash
   curl -I -X HEAD http://localhost:8000/pets
   ```
   The response will include an `API-Version` header, e.g., `API-Version: 1.0,2.0,3.0,3.1`.

2. **Specifying a Version**:
   Include the `API-Version` header in your request to specify which version you want to use.
   ```bash
   curl -H "API-Version: 2.0" http://localhost:8000/pets
   ```
   
3. **Version Not Supported**:
   If you request a version not supported by an endpoint, you'll receive a `406 Not Acceptable` response.
   ```bash
   # /shelters endpoint only supports v3.0 and above
   curl -H "API-Version: 1.0" http://localhost:8000/shelters
   ```

### How It Works Under the Hood

1. The `VersionNegotiationMiddleware` intercepts all requests and handles:
   - HEAD requests for version discovery
   - Validating that requested versions are supported
   - Storing the requested version in `request.state.api_version`

2. The `versioned_api_route` decorator and `VersionedAPIRouter` handle:
   - Registering endpoints with their supported versions
   - Applying appropriate request and response transformations

3. The shim system handles transformations between versions:
   - Request shims transform older version requests to the latest version format
   - Response shims transform latest version responses back to the requested version format

## Example Usage

### Getting All Pets

#### Using API v1.0
```bash
curl -H "API-Version: 1.0" http://localhost:8000/pets
```
Response will have the v1.0 format (age in years, no birth_date, limited species options, etc.)

#### Using API v3.1 (latest)
```bash
curl -H "API-Version: 3.1" http://localhost:8000/pets
```
Response will have the v3.1 format (age_months, birth_date, size, tags, health_status, etc.)

### Creating a Pet

#### Using API v1.0
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "API-Version: 1.0" \
  -d '{"name": "Fido", "species": "dog", "age": 3}' \
  http://localhost:8000/pets
```

#### Using API v3.1 (latest)
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "API-Version: 3.1" \
  -d '{"name": "Fido", "species": "dog", "age_months": 36, "size": "medium", "tags": ["friendly"], "health_status": "excellent"}' \
  http://localhost:8000/pets
```

### Accessing Version-Specific Endpoints

Some endpoints are only available in certain API versions:

```bash
# This works - shelters endpoint exists in v3.0+
curl -H "API-Version: 3.0" http://localhost:8000/shelters

# This fails with 406 Not Acceptable - shelters endpoint doesn't exist in v1.0
curl -H "API-Version: 1.0" http://localhost:8000/shelters
```

## Evolution of the API

Our API has evolved through several versions:

1. **v1.0**: Basic pet model with name, species (dog/cat/bird), and age in years.

2. **v2.0**: Added birth_date field and more species options (fish, reptile).

3. **v3.0**: 
   - Changed age from years to age_months for precision
   - Added size and tags fields
   - Added new species options (rabbit, hamster)
   - Introduced the /shelters endpoints

4. **v3.1**:
   - Added health_status field to the pet model

## Adding New API Versions

To add a new API version:

1. Define new data models for the version
2. Create shim functions to transform requests/responses between versions
3. Register the shims with the registry
4. Update route decorators to include the new version

## Development Guidelines

1. Always maintain backward compatibility when possible
2. Create clear shim transformations between adjacent versions
3. Document changes between versions
4. Use the version negotiation middleware for all API endpoints
5. Thoroughly test transformations between versions