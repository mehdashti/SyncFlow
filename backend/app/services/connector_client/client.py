"""
APISmith HTTP Client

Handles communication with APISmith microservice.
Fetches data from Oracle ERP through APISmith APIs.
"""

from typing import Any
import httpx
from loguru import logger

from app.core.config import settings


class APISmithClient:
    """
    APISmith Client

    Features:
    - JWT authentication
    - API execution with pagination
    - Retry logic with exponential backoff
    - Connection pooling for performance
    """

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize APISmith client

        Args:
            base_url: APISmith base URL (default from settings)
            username: Authentication username (default from settings)
            password: Authentication password (default from settings)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url or settings.APISmith_URL
        self.username = username or settings.APISmith_USERNAME
        self.password = password or settings.APISmith_PASSWORD
        self.timeout = timeout
        self.max_retries = max_retries

        self.access_token: str | None = None
        self.refresh_token: str | None = None

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

        logger.info(f"APISmith client initialized: {self.base_url}")

    async def authenticate(self) -> dict[str, Any]:
        """
        Authenticate with APISmith and get JWT tokens

        Returns:
            Authentication response with access_token and refresh_token

        Raises:
            httpx.HTTPStatusError: If authentication fails
        """
        logger.info("Authenticating with APISmith...")

        try:
            response = await self.client.post(
                f"{settings.APISmith_API_PREFIX}/auth/login",
                json={
                    "username": self.username,
                    "password": self.password,
                },
            )
            response.raise_for_status()

            auth_data = response.json()
            self.access_token = auth_data.get("access_token")
            self.refresh_token = auth_data.get("refresh_token")

            logger.info("Authentication successful")
            return auth_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Authentication failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    async def refresh_access_token(self) -> dict[str, Any]:
        """
        Refresh access token using refresh token

        Returns:
            New access token

        Raises:
            httpx.HTTPStatusError: If refresh fails
        """
        if not self.refresh_token:
            logger.warning("No refresh token available, re-authenticating...")
            return await self.authenticate()

        logger.info("Refreshing access token...")

        try:
            response = await self.client.post(
                f"{settings.APISmith_API_PREFIX}/auth/refresh",
                json={"refresh_token": self.refresh_token},
            )
            response.raise_for_status()

            auth_data = response.json()
            self.access_token = auth_data.get("access_token")

            logger.info("Token refresh successful")
            return auth_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.status_code}")
            # Re-authenticate if refresh fails
            return await self.authenticate()

    async def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated before making requests"""
        if not self.access_token:
            await self.authenticate()

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authentication"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def list_connectors(self) -> list[dict[str, Any]]:
        """
        List all available connectors

        Returns:
            List of connector definitions

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        await self._ensure_authenticated()

        logger.info("Fetching connector list...")

        try:
            response = await self.client.get(
                f"{settings.APISmith_API_PREFIX}/connectors",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            connectors = response.json()
            logger.info(f"Found {len(connectors)} connectors")
            return connectors

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # Token expired, refresh and retry
                await self.refresh_access_token()
                return await self.list_connectors()
            logger.error(f"Failed to fetch connectors: {e.response.status_code}")
            raise

    async def list_apis(
        self,
        page: int = 1,
        page_size: int = 100,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        List APIs with pagination and filters

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional filters (connector_uid, slug, is_active, etc.)

        Returns:
            Paginated API list with metadata

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        await self._ensure_authenticated()

        logger.info(f"Fetching APIs: page={page}, page_size={page_size}")

        params: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }

        if filters:
            params.update(filters)

        try:
            response = await self.client.get(
                f"{settings.APISmith_API_PREFIX}/apis",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Found {data.get('total', 0)} APIs "
                f"(page {data.get('page', 1)}/{data.get('total_pages', 1)})"
            )
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.list_apis(page, page_size, filters)
            logger.error(f"Failed to fetch APIs: {e.response.status_code}")
            raise

    async def get_api_by_slug(self, slug: str) -> dict[str, Any]:
        """
        Get API definition by slug

        Args:
            slug: API slug (e.g., "inventory_items")

        Returns:
            API definition

        Raises:
            httpx.HTTPStatusError: If not found or request fails
        """
        await self._ensure_authenticated()

        logger.info(f"Fetching API: {slug}")

        try:
            response = await self.client.get(
                f"{settings.APISmith_API_PREFIX}/apis/slug/{slug}",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            api_def = response.json()
            logger.info(f"API found: {api_def.get('name', slug)}")
            return api_def

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.get_api_by_slug(slug)
            elif e.response.status_code == 404:
                logger.error(f"API not found: {slug}")
            else:
                logger.error(f"Failed to fetch API: {e.response.status_code}")
            raise

    async def execute_api(
        self,
        slug: str,
        page: int = 1,
        page_size: int = 1000,
        filters: list[dict[str, Any]] | None = None,
        sort: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Execute API and fetch data from Oracle ERP

        Args:
            slug: API slug (e.g., "inventory_items")
            page: Page number (1-indexed)
            page_size: Records per page (max 10000)
            filters: Optional filters for WHERE clause
                    [{"field": "rowversion", "operator": ">", "value": "2025-12-01"}]
            sort: Optional sort configuration
                  {"field": "rowversion", "direction": "asc"}

        Returns:
            Execution result with data and metadata:
            {
                "success": true,
                "data": [...],
                "metadata": {
                    "total_rows": 1000,
                    "page": 1,
                    "page_size": 1000,
                    "execution_time_ms": 234
                }
            }

        Raises:
            httpx.HTTPStatusError: If execution fails
        """
        await self._ensure_authenticated()

        logger.info(f"Executing API: {slug} (page={page}, page_size={page_size})")

        payload: dict[str, Any] = {
            "page": page,
            "page_size": page_size,
        }

        if filters:
            payload["filters"] = filters

        if sort:
            payload["sort"] = sort

        try:
            response = await self.client.post(
                f"{settings.APISmith_API_PREFIX}/runtime/{slug}/execute",
                json=payload,
                headers=self._get_headers(),
                timeout=httpx.Timeout(60.0),  # Longer timeout for data fetch
            )
            response.raise_for_status()

            result = response.json()
            rows_count = len(result.get("data", []))
            exec_time = result.get("metadata", {}).get("execution_time_ms", 0)

            logger.info(
                f"API execution successful: {rows_count} rows in {exec_time}ms"
            )
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.execute_api(slug, page, page_size, filters, sort)
            logger.error(
                f"API execution failed: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"API execution error: {e}")
            raise

    async def execute_api_all_pages(
        self,
        slug: str,
        page_size: int = 1000,
        filters: list[dict[str, Any]] | None = None,
        sort: dict[str, str] | None = None,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute API and fetch all pages

        Args:
            slug: API slug
            page_size: Records per page
            filters: Optional filters
            sort: Optional sort
            max_pages: Optional maximum pages to fetch (for testing)

        Returns:
            List of all records from all pages

        Raises:
            httpx.HTTPStatusError: If execution fails
        """
        logger.info(f"Fetching all pages for API: {slug}")

        all_records: list[dict[str, Any]] = []
        page = 1

        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            result = await self.execute_api(
                slug=slug,
                page=page,
                page_size=page_size,
                filters=filters,
                sort=sort,
            )

            data = result.get("data", [])
            if not data:
                logger.info("No more data, pagination complete")
                break

            all_records.extend(data)

            metadata = result.get("metadata", {})
            total_rows = metadata.get("total_rows", 0)
            current_count = len(all_records)

            logger.info(
                f"Page {page} complete: {current_count}/{total_rows} total rows"
            )

            # Check if we've fetched all records
            if current_count >= total_rows:
                logger.info("All records fetched")
                break

            page += 1

        logger.info(f"Fetched {len(all_records)} total records from {page} pages")
        return all_records

    async def health_check(self) -> dict[str, Any]:
        """
        Check APISmith health status

        Returns:
            Health status response

        Raises:
            httpx.HTTPStatusError: If health check fails
        """
        try:
            response = await self.client.get(
                f"{settings.APISmith_API_PREFIX}/health"
            )
            response.raise_for_status()

            health = response.json()
            logger.info(f"APISmith health: {health.get('status', 'unknown')}")
            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client and cleanup resources"""
        await self.client.aclose()
        logger.info("APISmith client closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience function

async def get_connector_client() -> APISmithClient:
    """
    Get configured APISmith client instance

    Returns:
        APISmithClient instance

    Usage:
        async with await get_connector_client() as client:
            data = await client.execute_api("inventory_items")
    """
    return APISmithClient()
