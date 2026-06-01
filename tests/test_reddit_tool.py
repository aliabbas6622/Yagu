import pytest
from unittest.mock import patch, MagicMock
from product_idea_miner.tools.reddit_tool import scrape_reddit
from product_idea_miner.config.models import Source

@patch("product_idea_miner.tools.reddit_tool._has_reddit_api_config")
@patch("product_idea_miner.tools.reddit_tool._scrape_reddit_api")
def test_scrape_reddit_uses_api(mock_scrape_api, mock_has_config):
    mock_has_config.return_value = True
    mock_scrape_api.return_value = [MagicMock()]

    results = scrape_reddit(["SaaS"], ["I wish there was"])

    assert mock_scrape_api.called
    assert len(results) == 1

@patch("product_idea_miner.tools.reddit_tool._has_reddit_api_config")
@patch("product_idea_miner.tools.reddit_tool._scrape_reddit_with_scrapling")
@patch("product_idea_miner.tools.reddit_tool.REDDIT_USE_SCRAPLING_FALLBACK", True)
def test_scrape_reddit_falls_back_to_scrapling(mock_scrapling, mock_has_config):
    mock_has_config.return_value = False
    mock_scrapling.return_value = [MagicMock()]

    results = scrape_reddit(["SaaS"], ["I wish there was"])

    assert mock_scrapling.called
    assert len(results) == 1

def test_scrape_reddit_api_logic():
    mock_reddit = MagicMock()
    mock_subreddit = MagicMock()
    mock_post = MagicMock()

    mock_post.score = 20
    mock_post.url = "https://reddit.com/r/SaaS/comments/1"
    mock_post.title = "Test Post"
    mock_post.selftext = "Test Body"
    mock_post.num_comments = 5
    mock_post.created_utc = 1672531200

    mock_reddit.subreddit.return_value = mock_subreddit
    mock_subreddit.search.return_value = [mock_post]

    with patch("praw.Reddit", return_value=mock_reddit):
        from product_idea_miner.tools.reddit_tool import _scrape_reddit_api
        results = _scrape_reddit_api(["SaaS"], ["keyword"], 1)

        assert len(results) == 1
        assert results[0].title == "Test Post"
        assert results[0].upvotes == 20

@patch("scrapling.fetchers.Fetcher")
def test_scrape_reddit_scrapling_logic(mock_fetcher):
    mock_page = MagicMock()
    mock_result = MagicMock()

    mock_page.status = 200
    mock_page.css.return_value = [mock_result]

    # More specific side effects for scrapling parse logic
    def mock_css_side_effect(selector):
        m = MagicMock()
        if "a.search-title::text" in selector:
            m.get.return_value = "Test Title"
        elif "a.search-title::attr(href)" in selector:
            m.get.return_value = "/r/SaaS/comments/1"
        elif "span.search-score::text" in selector:
            m.get.return_value = "20 points"
        elif "a.search-comments::text" in selector:
            m.get.return_value = "5 comments"
        elif "span.search-time time::attr(datetime)" in selector:
            m.get.return_value = "2023-01-01T00:00:00Z"
        elif "div.md p::text" in selector:
            m.get.return_value = "Test Body"
        return m

    mock_result.css.side_effect = mock_css_side_effect
    mock_fetcher.get.return_value = mock_page

    with patch("product_idea_miner.tools.reddit_tool.MIN_UPVOTES", 10):
        from product_idea_miner.tools.reddit_tool import _scrape_reddit_with_scrapling
        results = _scrape_reddit_with_scrapling(["SaaS"], ["keyword"], 1)

        assert len(results) == 1
        assert results[0].title == "Test Title"
        assert results[0].upvotes == 20
