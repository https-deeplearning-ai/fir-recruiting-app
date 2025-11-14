"""
Company ID Cache Service
Caches company_name → coresignal_id mappings to save API search credits
"""
import re
from typing import Optional, Dict, Any
from datetime import datetime
import httpx


class CompanyIDCacheService:
    """Service for caching and retrieving company CoreSignal ID mappings."""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

    def normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for matching.
        - Lowercase
        - Remove punctuation except hyphens
        - Remove common suffixes (Inc, LLC, Corp, etc.)
        - Strip whitespace
        """
        if not name:
            return ""

        # Lowercase
        name = name.lower()

        # Remove common company suffixes
        suffixes = [
            r'\s+inc\.?$', r'\s+incorporated$', r'\s+llc\.?$',
            r'\s+ltd\.?$', r'\s+limited$', r'\s+corp\.?$',
            r'\s+corporation$', r'\s+co\.?$', r'\s+company$',
            r'\s+gmbh$', r'\s+ag$', r'\s+pte\.?$', r'\s+pty\.?$'
        ]
        for suffix in suffixes:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)

        # Remove punctuation except hyphens
        name = re.sub(r'[^\w\s\-]', '', name)

        # Remove extra whitespace
        name = ' '.join(name.split())

        return name.strip()

    async def get_cached_id(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached CoreSignal ID for a company.
        Returns: Dict with company_id (CoreSignal ID) if found, else None

        Uses EXISTING company_lookup_cache table schema:
        - company_id (not coresignal_id)
        - lookup_successful (boolean)
        - No lookup_tier or normalized names
        """
        if not company_name:
            return None

        try:
            async with httpx.AsyncClient() as client:
                # Query cache by company_name
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/company_lookup_cache",
                    headers=self.headers,
                    params={
                        "company_name": f"eq.{company_name}",
                        "select": "id,company_id,lookup_successful,confidence,employee_count,created_at,last_used_at"
                    }
                )

                if response.status_code == 200:
                    results = response.json()
                    if results:
                        cache_entry = results[0]

                        # Update last_used_at
                        await self._update_last_used(cache_entry.get("id") or company_name)

                        # Return data for both successful AND failed lookups
                        return {
                            "coresignal_id": cache_entry.get("company_id"),  # Can be None for failed searches
                            "company_id": cache_entry.get("company_id"),
                            "lookup_successful": cache_entry.get("lookup_successful"),
                            "confidence": cache_entry.get("confidence"),
                            "employee_count": cache_entry.get("employee_count"),
                            "created_at": cache_entry.get("created_at"),
                            "last_used_at": cache_entry.get("last_used_at"),
                            "from_cache": True
                        }

        except Exception as e:
            print(f"[CACHE] Error retrieving cached ID for {company_name}: {e}")

        return None

    async def save_to_cache(
        self,
        company_name: str,
        coresignal_id: Optional[int],
        lookup_tier: Optional[str] = None,  # Not used in existing schema
        website: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a company name → CoreSignal ID mapping to cache.

        Uses EXISTING company_lookup_cache table schema:
        - company_id (maps from coresignal_id parameter)
        - lookup_successful (True if ID found, False if None)
        - website, confidence, employee_count

        Args:
            company_name: Company name
            coresignal_id: CoreSignal ID (None for failed lookups)
            lookup_tier: (ignored, for API compatibility)
            website: Company website
            metadata: Additional data (can include confidence, employee_count)

        Returns: True if saved successfully
        """
        if not company_name:
            return False

        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "company_name": company_name,
                    "company_id": coresignal_id,  # Use correct field name
                    "lookup_successful": coresignal_id is not None,
                    "website": website,
                    "confidence": metadata.get("confidence", "1.00") if metadata else "1.00",
                    "employee_count": metadata.get("employee_count") if metadata else None,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_used_at": datetime.utcnow().isoformat()
                }

                # Upsert (insert or update if exists)
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/company_lookup_cache",
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=data
                )

                if response.status_code in [200, 201]:
                    status = "✅" if coresignal_id else "❌"
                    print(f"[CACHE] {status} Saved {company_name} → {coresignal_id}")
                    return True
                else:
                    print(f"[CACHE] ❌ Failed to save {company_name}: {response.status_code} {response.text}")

        except Exception as e:
            print(f"[CACHE] Error saving {company_name} to cache: {e}")

        return False

    async def _update_last_used(self, identifier):
        """Update last_used_at for a cache entry.

        Args:
            identifier: Either entry ID or company_name
        """
        try:
            async with httpx.AsyncClient() as client:
                # Try to update by ID first, fallback to company_name
                if isinstance(identifier, int):
                    params = {"id": f"eq.{identifier}"}
                else:
                    params = {"company_name": f"eq.{identifier}"}

                await client.patch(
                    f"{self.supabase_url}/rest/v1/company_lookup_cache",
                    headers=self.headers,
                    params=params,
                    json={"last_used_at": datetime.utcnow().isoformat()}
                )

        except Exception as e:
            print(f"[CACHE] Error updating last_used: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/company_lookup_cache",
                    headers=self.headers,
                    params={"select": "id,lookup_successful,confidence"}
                )

                if response.status_code == 200:
                    results = response.json()
                    total_entries = len(results)
                    successful = sum(1 for r in results if r.get("lookup_successful"))
                    failed = total_entries - successful

                    # Average confidence
                    confidences = [float(r.get("confidence", 0)) for r in results if r.get("lookup_successful") and r.get("confidence")]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                    return {
                        "total_entries": total_entries,
                        "successful_lookups": successful,
                        "failed_lookups": failed,
                        "average_confidence": f"{avg_confidence:.2f}",
                        "estimated_credits_saved": successful  # 1 search credit per successful cached lookup
                    }

        except Exception as e:
            print(f"[CACHE] Error getting stats: {e}")

        return {"error": str(e)}
