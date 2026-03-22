"""LinkedIn via Apify (Phase 4)."""

from __future__ import annotations

import os

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ApifyInput(BaseModel):
    search_query: str = Field(description="LinkedIn search query")
    max_results: int = Field(default=10, ge=1, le=100)


class ApifyTool(BaseTool):
    name: str = "ApifyScrapeTool"
    description: str = "Scrapes LinkedIn profiles using Apify (requires APIFY_API_TOKEN)."
    args_schema: type[BaseModel] = ApifyInput

    def _run(self, search_query: str, max_results: int = 10) -> list[dict] | dict:
        token = os.getenv("APIFY_API_TOKEN")
        if not token:
            return {
                "error": "APIFY_API_TOKEN not set",
                "raw_text": "",
                "source_type": "linkedin",
            }
        try:
            from apify_client import ApifyClient

            actor_id = os.getenv("APIFY_ACTOR_ID", "bebity/linkedin-premium-actor")
            client = ApifyClient(token)
            run = client.actor(actor_id).call(
                run_input={
                    "searchQueries": [search_query],
                    "maxResults": max_results,
                    "scrapeType": "profiles",
                }
            )
            profiles = list(client.dataset(run["defaultDatasetId"]).iterate_items())
            return [
                {"raw_text": self._profile_to_text(p), "source_type": "linkedin", "profile": p}
                for p in profiles
            ]
        except Exception as e:  # noqa: BLE001
            return {
                "error": str(e),
                "raw_text": "",
                "source_type": "linkedin",
                "profiles": [],
            }

    @staticmethod
    def _profile_to_text(profile: dict) -> str:
        return (
            f"Name: {profile.get('fullName', '')}\n"
            f"Title: {profile.get('headline', '')}\n"
            f"Location: {profile.get('location', '')}\n"
            f"Summary: {profile.get('summary', '')}\n"
            f"Experience: {profile.get('experience', '')}\n"
            f"Skills: {profile.get('skills', '')}\n"
            f"Education: {profile.get('education', '')}"
        )
