import pytest
from unittest.mock import patch, MagicMock
from product_idea_miner.tools.webhook_tool import send_to_discord, send_to_slack
from product_idea_miner.config.models import IdeaRecord, Source, ProductIdea
from datetime import datetime

@pytest.fixture
def sample_idea():
    return IdeaRecord(
        source=Source.REDDIT,
        original_url="https://test.com",
        post_title="Test Title",
        post_body="Test Body",
        problem_summary="Test Summary",
        urgency_score=10,
        frequency_score=10,
        monetization_score=10,
        total_score=30,
        product_ideas=[ProductIdea(idea="Test Idea", type="SaaS", description="Test Desc")],
        category="Productivity",
        target_audience="Devs",
        date_found=datetime.now()
    )

@patch("product_idea_miner.tools.webhook_tool.DISCORD_WEBHOOK_URL", "https://discord.webhook")
@patch("product_idea_miner.tools.webhook_tool._post_webhook")
def test_send_to_discord(mock_post, sample_idea):
    send_to_discord(sample_idea)

    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert args[0] == "https://discord.webhook"
    assert "embeds" in args[1]
    assert args[1]["embeds"][0]["title"] == "New Product Idea: Test Summary"

@patch("product_idea_miner.tools.webhook_tool.SLACK_WEBHOOK_URL", "https://slack.webhook")
@patch("product_idea_miner.tools.webhook_tool._post_webhook")
def test_send_to_slack(mock_post, sample_idea):
    send_to_slack(sample_idea)

    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert args[0] == "https://slack.webhook"
    assert "blocks" in args[1]
    assert "Test Summary" in str(args[1]["blocks"])

@patch("product_idea_miner.tools.webhook_tool.DISCORD_WEBHOOK_URL", None)
@patch("product_idea_miner.tools.webhook_tool._post_webhook")
def test_send_to_discord_no_url(mock_post, sample_idea):
    send_to_discord(sample_idea)
    assert not mock_post.called
