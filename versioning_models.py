from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Set, TypeVar, Generic, Type, Optional, Callable, Any, Union, cast
import re
from pydantic import BaseModel, Field, validator


class ApiVersion:
    """Represents an API version in major.minor format."""

    _version_pattern = re.compile(r'^(\d+)\.(\d+)$')

    def __init__(self, version_str: str):
        match = self._version_pattern.match(version_str)
        if not match:
            raise ValueError(f"Invalid version format: {version_str}. Expected format: major.minor")

        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self._version_str = version_str

    def __str__(self) -> str:
        return self._version_str

    def __repr__(self) -> str:
        return f"ApiVersion('{self._version_str}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApiVersion):
            return False
        return self.major == other.major and self.minor == other.minor

    def __hash__(self) -> int:
        return hash((self.major, self.minor))

    def __lt__(self, other: 'ApiVersion') -> bool:
        if self.major < other.major:
            return True
        if self.major > other.major:
            return False
        return self.minor < other.minor


class VersionedEndpoint:
    """Tracks versions supported by an endpoint."""

    def __init__(self, path: str, supported_versions: List[ApiVersion]):
        self.path = path
        self.supported_versions = sorted(supported_versions)

    def supports_version(self, version: ApiVersion) -> bool:
        """Check if the endpoint supports the specified version."""
        return version in self.supported_versions

    def get_latest_version(self) -> ApiVersion:
        """Get the latest supported version for this endpoint."""
        if not self.supported_versions:
            raise ValueError(f"No versions defined for endpoint {self.path}")
        return self.supported_versions[-1]

    def get_version_chain(self, from_version: ApiVersion) -> List[ApiVersion]:
        """
        Get the chain of versions from from_version to the latest version.
        Used for determining which shims to apply.
        """
        if not self.supports_version(from_version):
            raise ValueError(f"Version {from_version} not supported for endpoint {self.path}")

        idx = self.supported_versions.index(from_version)
        return self.supported_versions[idx:]


# Registry to track endpoint versions and their supported versions
class VersionRegistry:
    """Registry of all versioned endpoints."""

    def __init__(self):
        self._endpoints: Dict[str, VersionedEndpoint] = {}

    def register_endpoint(self, path: str, version: ApiVersion) -> None:
        """Register an endpoint with a supported version."""
        if path in self._endpoints:
            self._endpoints[path].supported_versions.append(version)
            self._endpoints[path].supported_versions.sort()  # Keep versions sorted
        else:
            self._endpoints[path] = VersionedEndpoint(path, [version])

    def get_endpoint(self, path: str) -> Optional[VersionedEndpoint]:
        """Get the versioned endpoint for a path."""
        return self._endpoints.get(path)

    def get_supported_versions(self, path: str) -> List[ApiVersion]:
        """Get all supported versions for an endpoint."""
        endpoint = self.get_endpoint(path)
        if not endpoint:
            return []
        return endpoint.supported_versions

    def supports_version(self, path: str, version: ApiVersion) -> bool:
        """Check if an endpoint supports a specific version."""
        endpoint = self.get_endpoint(path)
        if not endpoint:
            return False
        return endpoint.supports_version(version)


# We'll use a singleton registry across the application
version_registry = VersionRegistry()


# Models for the versioning middleware
class VersionNegotiationError(Exception):
    """Exception raised when version negotiation fails."""
    pass


# Type for request shim functions
RequestT = TypeVar('RequestT', bound=BaseModel)
ResponseT = TypeVar('ResponseT', bound=BaseModel)

# Type definitions for shim functions
RequestShimFn = Callable[[Any], Any]  # Request transformation function
ResponseShimFn = Callable[[Any], Any]  # Response transformation function


# Registry for shim functions
class ShimRegistry:
    """Registry for request/response transformation functions between versions."""

    def __init__(self):
        # (path, from_version, to_version) -> (request_shim, response_shim)
        self._request_shims: Dict[tuple[str, ApiVersion, ApiVersion], RequestShimFn] = {}
        self._response_shims: Dict[tuple[str, ApiVersion, ApiVersion], ResponseShimFn] = {}

    def register_request_shim(self, path: str, from_version: ApiVersion,
                              to_version: ApiVersion, shim_fn: RequestShimFn) -> None:
        """Register a request transformation function between versions."""
        key = (path, from_version, to_version)
        self._request_shims[key] = shim_fn

    def register_response_shim(self, path: str, from_version: ApiVersion,
                               to_version: ApiVersion, shim_fn: ResponseShimFn) -> None:
        """Register a response transformation function between versions."""
        key = (path, from_version, to_version)
        self._response_shims[key] = shim_fn

    def get_request_shim(self, path: str, from_version: ApiVersion,
                         to_version: ApiVersion) -> Optional[RequestShimFn]:
        """Get the request transformation function for a path between versions."""
        key = (path, from_version, to_version)
        return self._request_shims.get(key)

    def get_response_shim(self, path: str, from_version: ApiVersion,
                          to_version: ApiVersion) -> Optional[ResponseShimFn]:
        """Get the response transformation function for a path between versions."""
        key = (path, from_version, to_version)
        return self._response_shims.get(key)


# Singleton shim registry
shim_registry = ShimRegistry()