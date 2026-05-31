import requests
from typing import List
from product_idea_miner.config.models import IdeaRecord
from product_idea_miner.config.settings import DISCORD_WEBHOOK_URL, SLACK_WEBHOOK_URL

def send_to_discord(idea: IdeaRecord):
    """
    Sends a single idea to a Discord webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        return

    embed = {
        "title": f"New Product Idea: {idea.problem_summary}",
        "url": idea.original_url,
        "color": 3447003, # Blue
        "fields": [
            {"name": "Source", "value": idea.source.value, "inline": True},
            {"name": "Category", "value": idea.category, "inline": True},
            {"name": "Total Score", "value": f"{idea.total_score}/30", "inline": True},
            {"name": "Target Audience", "value": idea.target_audience}
        ],
        "description": "**Top Product Ideas:**\n" + "\n".join([f"• **{p.idea}** ({p.type}): {p.description}" for p in idea.product_ideas])
    }

    payload = {"embeds": [embed]}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Failed to send to Discord: {e}")

def send_to_slack(idea: IdeaRecord):
    """
    Sends a single idea to a Slack webhook.
    """
    if not SLACK_WEBHOOK_URL:
        return

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*New Product Idea found on {idea.source.value}*\n*Problem:* {idea.problem_summary}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Category:*\n{idea.category}"},
                {"type": "mrkdwn", "text": f"*Total Score:*\n{idea.total_score}/30"}
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Product Ideas:*\n" + "\n".join([f"• *{p.idea}* ({p.type}): {p.description}" for p in idea.product_ideas])
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Post"},
                    "url": idea.original_url
                }
            ]
        }
    ]

    payload = {"blocks": blocks}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Failed to send to Slack: {e}")

def notify_all(idea: IdeaRecord):
    send_to_discord(idea)
    send_to_slack(idea)
