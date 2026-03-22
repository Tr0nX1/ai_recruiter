"""Slack notifications (optional)."""

from __future__ import annotations

import os

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SlackInput(BaseModel):
    message: str = Field(description="Message to post to Slack")


class SlackNotifyTool(BaseTool):
    name: str = "SlackNotifyTool"
    description: str = "Sends a message to Slack when a candidate is shortlisted (needs SLACK_BOT_TOKEN)."
    args_schema: type[BaseModel] = SlackInput

    def _run(self, message: str) -> dict:
        token = os.getenv("SLACK_BOT_TOKEN")
        channel = os.getenv("SLACK_CHANNEL_ID")
        if not token or not channel:
            return {"sent": False, "reason": "Slack not configured"}
        try:
            from slack_sdk import WebClient

            client = WebClient(token=token)
            blocks = [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": message[:2900]},
                }
            ]
            client.chat_postMessage(channel=channel, text=message[:4000], blocks=blocks)
            return {"sent": True}
        except Exception as e:  # noqa: BLE001
            return {"sent": False, "error": str(e)}
