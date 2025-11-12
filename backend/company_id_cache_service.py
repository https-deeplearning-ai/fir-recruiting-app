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
        Returns: Dict with coresignal_id, lookup_tier, metadata if found, else None
        """
        normalized_name = self.normalize_company_name(company_name)

        if not normalized_name:
            return None

        try:
            async with httpx.AsyncClient() as client:
                # Query cache
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/company_id_cache",
                    headers=self.headers,
                    params={
                        "company_name_normalized": f"eq.{normalized_name}",
                        "select": "coresignal_id,lookup_tier,metadata,hit_count"
                    }
                )

                if response.status_code == 200:
                    results = response.json()
                    if results:
                        cache_entry = results[0]

                        # Update hit_count and last_accessed_at
                        await self._increment_hit_count(cache_entry['coresignal_id'])

                        return {
                            "coresignal_id": cache_entry["coresignal_id"],
                            "lookup_tier": cache_entry["lookup_tier"],
                            "metadata": cache_entry.get("metadata", {}),
                            "hit_count": cache_entry.get("hit_count", 0) + 1,
                            "from_cache": True
                        }

        except Exception as e:
            print(f"[CACHE] Error retrieving cached ID for {company_name}: {e}")

        return None

    async def save_to_cache(
        self,
        company_name: str,
        coresignal_id: int,
        lookup_tier: str,
        website: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save a company name → CoreSignal ID mapping to cache.
        Returns: True if saved successfully, False otherwise
        """
        normalized_name = self.normalize_company_name(company_name)

        if not normalized_name or not coresignal_id:
            return False

        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "company_name": company_name,
                    "company_name_normalized": normalized_name,
                    "coresignal_id": coresignal_id,
                    "lookup_tier": lookup_tier,
                    "website": website,
                    "metadata": metadata or {},
                    "hit_count": 0,
                    "last_accessed_at": datetime.utcnow().isoformat()
                }

                # Upsert (insert or update if exists)
                response = await client.post(
                    f"{self.supabase_url}/rest/v1/company_id_cache",
                    headers={**self.headers, "Prefer": "resolution=merge-duplicates"},
                    json=data
                )

                if response.status_code in [200, 201]:
                    print(f"[CACHE] ✅ Saved {company_name} → {coresignal_id} (tier: {lookup_tier})")
                    return True
                else:
                    print(f"[CACHE] ❌ Failed to save {company_name}: {response.status_code} {response.text}")

        except Exception as e:
            print(f"[CACHE] Error saving {company_name} to cache: {e}")

        return False

    async def _increment_hit_count(self, coresignal_id: int):
        """Increment hit_count and update last_accessed_at for a cache entry."""
        try:
            async with httpx.AsyncClient() as client:
                # Get current hit_count
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/company_id_cache",
                    headers=self.headers,
                    params={
                        "coresignal_id": f"eq.{coresignal_id}",
                        "select": "id,hit_count"
                    }
                )

                if response.status_code == 200:
                    results = response.json()
                    if results:
                        entry_id = results[0]["id"]
                        current_hits = results[0].get("hit_count", 0)

                        # Update
                        await client.patch(
                            f"{self.supabase_url}/rest/v1/company_id_cache",
                            headers=self.headers,
                            params={"id": f"eq.{entry_id}"},
                            json={
                                "hit_count": current_hits + 1,
                                "last_accessed_at": datetime.utcnow().isoformat()
                            }
                        )

        except Exception as e:
            print(f"[CACHE] Error updating hit count: {e}")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.supabase_url}/rest/v1/company_id_cache",
                    headers=self.headers,
                    params={"select": "id,hit_count,lookup_tier"}
                )

                if response.status_code == 200:
                    results = response.json()
                    total_entries = len(results)
                    total_hits = sum(r.get("hit_count", 0) for r in results)

                    # Count by tier
                    tier_counts = {}
                    for r in results:
                        tier = r.get("lookup_tier", "unknown")
                        tier_counts[tier] = tier_counts.get(tier, 0) + 1

                    return {
                        "total_entries": total_entries,
                        "total_cache_hits": total_hits,
                        "estimated_credits_saved": total_hits,  # 1 search credit per hit avoided
                        "tier_distribution": tier_counts
                    }

        except Exception as e:
            print(f"[CACHE] Error getting stats: {e}")

        return {"error": str(e)}
