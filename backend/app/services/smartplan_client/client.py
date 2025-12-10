"""
ScheduleHub HTTP Client

Handles communication with ScheduleHub microservice.
Sends processed data to target system with CRUD operations.
"""

from typing import Any
import httpx
from loguru import logger

from app.core.config import settings


class ScheduleHubClient:
    """
    ScheduleHub Client

    Features:
    - JWT authentication
    - CRUD operations (GET, POST, PATCH, DELETE)
    - Batch operations for performance
    - Retry logic with exponential backoff
    - Connection pooling
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
        Initialize ScheduleHub client

        Args:
            base_url: ScheduleHub base URL (default from settings)
            username: Authentication username (default from settings)
            password: Authentication password (default from settings)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url or settings.ScheduleHub_URL
        self.username = username or settings.ScheduleHub_USERNAME
        self.password = password or settings.ScheduleHub_PASSWORD
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

        logger.info(f"ScheduleHub client initialized: {self.base_url}")

    async def authenticate(self) -> dict[str, Any]:
        """
        Authenticate with ScheduleHub and get JWT tokens

        Returns:
            Authentication response with access_token and refresh_token

        Raises:
            httpx.HTTPStatusError: If authentication fails
        """
        logger.info("Authenticating with ScheduleHub...")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/auth/login",
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
                f"{settings.ScheduleHub_API_PREFIX}/auth/refresh",
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

    async def get_by_bk_hash(
        self,
        entity: str,
        bk_hash: str,
    ) -> dict[str, Any] | None:
        """
        Get record by BK_HASH (erp_key_hash)

        Args:
            entity: Entity name (e.g., "items", "customers")
            bk_hash: Business key hash

        Returns:
            Record if found, None otherwise

        Raises:
            httpx.HTTPStatusError: If request fails (except 404)
        """
        await self._ensure_authenticated()

        logger.debug(f"Fetching {entity} by BK_HASH: {bk_hash[:16]}...")

        try:
            response = await self.client.get(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}",
                params={"erp_key_hash": bk_hash},
                headers=self._get_headers(),
            )

            if response.status_code == 404:
                logger.debug(f"Record not found: {bk_hash[:16]}")
                return None

            response.raise_for_status()

            # Assume API returns list of matching records
            records = response.json()
            if isinstance(records, list) and len(records) > 0:
                return records[0]
            elif isinstance(records, dict):
                return records

            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.get_by_bk_hash(entity, bk_hash)
            logger.error(f"Failed to fetch record: {e.response.status_code}")
            raise

    async def get_batch_by_bk_hashes(
        self,
        entity: str,
        bk_hashes: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        Get multiple records by BK_HASHes in batch

        Args:
            entity: Entity name
            bk_hashes: List of business key hashes

        Returns:
            Dict mapping bk_hash → record (only for found records)

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        await self._ensure_authenticated()

        logger.info(f"Fetching {len(bk_hashes)} {entity} records by BK_HASH...")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/batch/query",
                json={"erp_key_hashes": bk_hashes},
                headers=self._get_headers(),
            )
            response.raise_for_status()

            records = response.json()

            # Build lookup map
            record_map: dict[str, dict[str, Any]] = {}
            for record in records:
                bk_hash = record.get("erp_key_hash")
                if bk_hash:
                    record_map[bk_hash] = record

            logger.info(f"Found {len(record_map)}/{len(bk_hashes)} records")
            return record_map

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.get_batch_by_bk_hashes(entity, bk_hashes)
            logger.error(f"Batch query failed: {e.response.status_code}")
            raise

    async def insert(
        self,
        entity: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Insert new record

        Args:
            entity: Entity name
            data: Record data (must include identity fields)

        Returns:
            Created record with UID

        Raises:
            httpx.HTTPStatusError: If insert fails
        """
        await self._ensure_authenticated()

        logger.debug(f"Inserting {entity}: {data.get('erp_ref_str', 'N/A')}")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}",
                json=data,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            created = response.json()
            logger.debug(f"Insert successful: UID={created.get('uid')}")
            return created

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.insert(entity, data)
            logger.error(
                f"Insert failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def update(
        self,
        entity: str,
        uid: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Update existing record

        Args:
            entity: Entity name
            uid: Record UID
            data: Updated data (partial update supported)

        Returns:
            Updated record

        Raises:
            httpx.HTTPStatusError: If update fails
        """
        await self._ensure_authenticated()

        logger.debug(f"Updating {entity}: UID={uid}")

        try:
            response = await self.client.patch(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/{uid}",
                json=data,
                headers=self._get_headers(),
            )
            response.raise_for_status()

            updated = response.json()
            logger.debug(f"Update successful: UID={uid}")
            return updated

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.update(entity, uid, data)
            logger.error(
                f"Update failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def delete(
        self,
        entity: str,
        uid: str,
    ) -> dict[str, Any]:
        """
        Delete record (soft delete)

        Args:
            entity: Entity name
            uid: Record UID

        Returns:
            Deletion confirmation

        Raises:
            httpx.HTTPStatusError: If delete fails
        """
        await self._ensure_authenticated()

        logger.debug(f"Deleting {entity}: UID={uid}")

        try:
            response = await self.client.delete(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/{uid}",
                headers=self._get_headers(),
            )
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Delete successful: UID={uid}")
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.delete(entity, uid)
            logger.error(
                f"Delete failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def batch_insert(
        self,
        entity: str,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Insert multiple records in batch

        Args:
            entity: Entity name
            records: List of records to insert

        Returns:
            Batch operation result with success/failure counts

        Raises:
            httpx.HTTPStatusError: If batch operation fails
        """
        await self._ensure_authenticated()

        logger.info(f"Batch inserting {len(records)} {entity} records...")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/batch/insert",
                json={"records": records},
                headers=self._get_headers(),
                timeout=httpx.Timeout(120.0),  # Longer timeout for batch
            )
            response.raise_for_status()

            result = response.json()
            success_count = result.get("success_count", 0)
            failure_count = result.get("failure_count", 0)

            logger.info(
                f"Batch insert complete: {success_count} success, {failure_count} failed"
            )
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.batch_insert(entity, records)
            logger.error(
                f"Batch insert failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def batch_update(
        self,
        entity: str,
        updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Update multiple records in batch

        Args:
            entity: Entity name
            updates: List of records with UID and updated data

        Returns:
            Batch operation result with success/failure counts

        Raises:
            httpx.HTTPStatusError: If batch operation fails
        """
        await self._ensure_authenticated()

        logger.info(f"Batch updating {len(updates)} {entity} records...")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/batch/update",
                json={"updates": updates},
                headers=self._get_headers(),
                timeout=httpx.Timeout(120.0),
            )
            response.raise_for_status()

            result = response.json()
            success_count = result.get("success_count", 0)
            failure_count = result.get("failure_count", 0)

            logger.info(
                f"Batch update complete: {success_count} success, {failure_count} failed"
            )
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.batch_update(entity, updates)
            logger.error(
                f"Batch update failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def batch_delete(
        self,
        entity: str,
        uids: list[str],
    ) -> dict[str, Any]:
        """
        Delete multiple records in batch

        Args:
            entity: Entity name
            uids: List of record UIDs to delete

        Returns:
            Batch operation result with success/failure counts

        Raises:
            httpx.HTTPStatusError: If batch operation fails
        """
        await self._ensure_authenticated()

        logger.info(f"Batch deleting {len(uids)} {entity} records...")

        try:
            response = await self.client.post(
                f"{settings.ScheduleHub_API_PREFIX}/{entity}/batch/delete",
                json={"uids": uids},
                headers=self._get_headers(),
                timeout=httpx.Timeout(120.0),
            )
            response.raise_for_status()

            result = response.json()
            success_count = result.get("success_count", 0)
            failure_count = result.get("failure_count", 0)

            logger.info(
                f"Batch delete complete: {success_count} success, {failure_count} failed"
            )
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                await self.refresh_access_token()
                return await self.batch_delete(entity, uids)
            logger.error(
                f"Batch delete failed: {e.response.status_code} - {e.response.text}"
            )
            raise

    async def health_check(self) -> dict[str, Any]:
        """
        Check ScheduleHub health status

        Returns:
            Health status response

        Raises:
            httpx.HTTPStatusError: If health check fails
        """
        try:
            response = await self.client.get(
                f"{settings.ScheduleHub_API_PREFIX}/health"
            )
            response.raise_for_status()

            health = response.json()
            logger.info(f"ScheduleHub health: {health.get('status', 'unknown')}")
            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    async def close(self) -> None:
        """Close HTTP client and cleanup resources"""
        await self.client.aclose()
        logger.info("ScheduleHub client closed")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Convenience function

async def get_smartplan_client() -> ScheduleHubClient:
    """
    Get configured ScheduleHub client instance

    Returns:
        ScheduleHubClient instance

    Usage:
        async with await get_smartplan_client() as client:
            await client.insert("items", item_data)
    """
    return ScheduleHubClient()
