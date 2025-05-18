from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.routing import APIRouter
from starlette.datastructures import URL
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
import functools
import inspect
from typing import List, Optional, Callable, Dict, Type, Any, Union, TypeVar, cast
import re

from versioning_models import (
    ApiVersion, version_registry, shim_registry, VersionNegotiationError
)

# Constants
API_VERSION_HEADER = "API-Version"


class VersionNegotiationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle API version negotiation."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # For HEAD requests, return available versions
        if request.method == "HEAD":
            path = self._normalize_path(request.url.path)

            # Get supported versions for this path
            versions = version_registry.get_supported_versions(path)
            response = Response()

            if versions:
                # Format versions as comma-separated string
                version_str = ",".join(str(v) for v in versions)
                response.headers[API_VERSION_HEADER] = version_str

            return response

        # Check if API-Version header is present
        version_header = request.headers.get(API_VERSION_HEADER)

        # If no version specified, process as normal
        # (will use the latest version in the route handler)
        if not version_header:
            return Response(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Missing required header: {API_VERSION_HEADER}"
            )
            # return await call_next(request)

        # Parse the requested version
        try:
            requested_version = ApiVersion(version_header)
        except ValueError:
            return Response(
                content=f"Invalid API-Version format: {version_header}. Expected format: major.minor",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Store the requested version in request state for access in route handlers
        request.state.api_version = requested_version

        # Check if this version is supported for this path
        path = self._normalize_path(request.url.path)
        if not version_registry.supports_version(path, requested_version):
            supported_versions = version_registry.get_supported_versions(path)
            version_str = ", ".join(str(v) for v in supported_versions)
            return Response(
                content=f"API version {requested_version} not supported for this endpoint. Supported versions: {version_str}",
                status_code=status.HTTP_406_NOT_ACCEPTABLE
            )

        # Continue processing the request
        response = await call_next(request)

        # Add the actual API version used to the response header
        if API_VERSION_HEADER not in response.headers:
            response.headers[API_VERSION_HEADER] = str(requested_version)

        return response

    def _normalize_path(self, path: str) -> str:
        """
        Normalize the path by removing any path parameters.
        For example: /pets/123 -> /pets/{pet_id}
        """
        # This is a simple implementation - you may need more sophisticated
        # path normalization depending on your routing patterns
        segments = path.split('/')
        normalized_segments = []

        for segment in segments:
            # Check if segment might be a path parameter (UUID, int, etc.)
            if re.match(r'^[0-9a-f-]+$', segment):
                # For now, we'll just detect UUID-like parameters
                # You might want to improve this logic based on your routing patterns
                normalized_segments.append("{id}")
            else:
                normalized_segments.append(segment)

        return '/'.join(normalized_segments)



class VersionedAPIRouter(APIRouter):
    """
    A FastAPI router with built-in versioning support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def equip_endpoint_with_shims():
        """
        A decorator factory that produces a decorator for FastAPI route methods.
        This registers the route with specific API versions and handles version negotiation.
        """

        def decorator(endpoint_handler: Callable):
            @functools.wraps(endpoint_handler)
            async def wrapper(*args, **kwargs):
                # Extract the request object
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if not request:
                    for value in kwargs.values():
                        if isinstance(value, Request):
                            request = value
                            break

                if not request:
                    # If can't find request object, just call the original handler
                    return await endpoint_handler(*args, **kwargs)

                # Get the requested version from the request state or use latest
                path = request.url.path
                endpoint = version_registry.get_endpoint(path)

                if not endpoint:
                    # This should not happen if routes are registered correctly
                    return await endpoint_handler(*args, **kwargs)

                requested_version = getattr(request.state, 'api_version', None)
                if requested_version is None:
                    # If no version specified, use the latest
                    requested_version = endpoint.get_latest_version()

                latest_version = endpoint.get_latest_version()

                # If using the latest version, no transformation needed
                if requested_version == latest_version:
                    return await endpoint_handler(*args, **kwargs)

                # Apply request transformation (shimming) if needed
                if "body" not in kwargs:
                    kwargs["body"] = await request.json()
                transformed_args = list(args)
                transformed_kwargs = dict(kwargs)

                # Get the chain of versions to apply shims through
                version_chain = endpoint.get_version_chain(requested_version)

                # Apply request shims (forward direction)
                for i in range(len(version_chain) - 1):
                    from_version = version_chain[i]
                    to_version = version_chain[i + 1]

                    request_shim = shim_registry.get_request_shim(path, from_version, to_version)
                    if request_shim:
                        # Apply the request transformation
                        # Note: For simplicity, we're assuming shims modify kwargs directly
                        # You might want to enhance this to handle more complex transformations
                        transformed_kwargs = request_shim(transformed_kwargs)

                # Call the handler with transformed parameters
                result = await endpoint_handler(*transformed_args, **transformed_kwargs)

                # Apply response shims (backward direction)
                for i in range(len(version_chain) - 1, 0, -1):
                    from_version = version_chain[i]
                    to_version = version_chain[i - 1]

                    response_shim = shim_registry.get_response_shim(path, from_version, to_version)
                    if response_shim:
                        # Apply the response transformation
                        result = response_shim(result)

                return result

            return wrapper

        return decorator

    def versioned_route(self, path: str, *versions: str, **kwargs):
        """"
        Create a versioned route for the given path.

        Args:
            path: The route path.
            versions: The API versions this route supports.
            **kwargs: Additional arguments to pass to the route decorator.
        """

        def decorator(endpoint_handler: Callable):
            # Register the endpoint with all specified versions
            for version in versions:
                version_obj = ApiVersion(version)
                version_registry.register_endpoint(path, version_obj)

            versioned_handler = self.equip_endpoint_with_shims()(endpoint_handler)

            # Register the route with FastAPI
            self.add_api_route(path, versioned_handler, **kwargs)
            return versioned_handler

        return decorator

    def versioned_get(self, path: str, *versions: str, **kwargs):
        """Shorthand for versioned GET routes."""
        return self.versioned_route(path, *versions, methods=["GET"], **kwargs)

    def versioned_post(self, path: str, *versions: str, **kwargs):
        """Shorthand for versioned POST routes."""
        return self.versioned_route(path, *versions, methods=["POST"], **kwargs)

    def versioned_put(self, path: str, *versions: str, **kwargs):
        """Shorthand for versioned PUT routes."""
        return self.versioned_route(path, *versions, methods=["PUT"], **kwargs)

    def versioned_delete(self, path: str, *versions: str, **kwargs):
        """Shorthand for versioned DELETE routes."""
        return self.versioned_route(path, *versions, methods=["DELETE"], **kwargs)

    def versioned_patch(self, path: str, *versions: str, **kwargs):
        """Shorthand for versioned PATCH routes."""
        return self.versioned_route(path, *versions, methods=["PATCH"], **kwargs)