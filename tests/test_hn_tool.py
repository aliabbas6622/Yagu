import pytest
from unittest.mock import patch, MagicMock
from product_idea_miner.tools.hn_tool import scrape_hn
from product_idea_miner.config.models import Source

def test_scrape_hn_success():
    mock_top_stories = [1, 2]
    mock_item_1 = {
        "id": 1,
        "title": "Ask HN: How to manage freelance invoices?",
        "text": "I'm struggling with manual invoicing...",
        "score": 100,
        "kids": [10, 11],
        "time": 1672531200 # 2023-01-01
    }
    mock_item_2 = {
        "id": 2,
        "title": "Show HN: My new invoicing tool",
        "text": "Check out this tool I built...",
        "score": 50,
        "kids": [],
        "time": 1672617600 # 2023-01-02
    }

    def mocked_get_json(url):
        if "topstories.json" in url:
            return mock_top_stories
        if "item/1.json" in url:
            return mock_item_1
        if "item/2.json" in url:
            return mock_item_2
        return None

    with patch("product_idea_miner.tools.hn_tool._get_json", side_effect=mocked_get_json):
        results = scrape_hn(limit=2)

        assert len(results) == 2
        assert results[0].source == Source.HN
        assert "Ask HN: How to manage freelance invoices?" in results[0].title
        assert results[0].upvotes == 100
        assert results[0].num_comments == 2

        assert results[1].source == Source.HN
        assert "Show HN: My new invoicing tool" in results[1].title
        assert results[1].upvotes == 50
        assert results[1].num_comments == 0

def test_scrape_hn_filters_non_ask_show():
    mock_top_stories = [3]
    mock_item_3 = {
        "id": 3,
        "title": "Just a regular news story",
        "text": "Not interesting for pain points",
        "score": 10,
        "kids": [],
        "time": 1672704000
    }

    with patch("product_idea_miner.tools.hn_tool._get_json") as mock_get:
        mock_get.side_effect = lambda url: mock_top_stories if "topstories.json" in url else mock_item_3
        results = scrape_hn(limit=1)
        assert len(results) == 0

def test_scrape_hn_error_handling():
    with patch("product_idea_miner.tools.hn_tool._get_json", side_effect=Exception("API Down")):
        results = scrape_hn(limit=5)
        assert results == []
