import json
import csv
import os
from datetime import datetime
from product_idea_miner.tools.export_tool import export_to_json, export_to_csv
from product_idea_miner.config.models import IdeaRecord, Source, ProductIdea

def test_export_to_json(tmp_path):
    filename = tmp_path / "test_ideas.json"
    ideas = [
        IdeaRecord(
            source=Source.REDDIT,
            original_url="https://reddit.com/r/SaaS/1",
            post_title="Test Post",
            post_body="Test Body",
            problem_summary="Test Summary",
            urgency_score=5,
            frequency_score=5,
            monetization_score=5,
            total_score=15,
            product_ideas=[ProductIdea(idea="Test Idea", type="SaaS", description="Test Desc")],
            category="Productivity",
            target_audience="Devs",
            date_found=datetime(2023, 1, 1)
        )
    ]

    export_to_json(ideas, str(filename))

    assert os.path.exists(filename)
    with open(filename, 'r') as f:
        data = json.load(f)

    assert len(data) == 1
    assert data[0]["original_url"] == "https://reddit.com/r/SaaS/1"
    assert data[0]["date_found"] == "2023-01-01T00:00:00"

def test_export_to_csv(tmp_path):
    filename = tmp_path / "test_ideas.csv"
    ideas = [
        IdeaRecord(
            source=Source.HN,
            original_url="https://news.ycombinator.com/item?id=1",
            post_title="HN Post",
            post_body="HN Body",
            problem_summary="HN Summary",
            urgency_score=8,
            frequency_score=8,
            monetization_score=8,
            total_score=24,
            product_ideas=[ProductIdea(idea="HN Idea", type="SaaS", description="HN Desc")],
            category="Dev Tools",
            target_audience="Founders",
            date_found=datetime(2023, 1, 2)
        )
    ]

    export_to_csv(ideas, str(filename))

    assert os.path.exists(filename)
    with open(filename, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["original_url"] == "https://news.ycombinator.com/item?id=1"
    assert rows[0]["source"] == "hn"
    assert rows[0]["date_found"] == "2023-01-02T00:00:00"

def test_export_to_csv_empty(tmp_path):
    filename = tmp_path / "empty.csv"
    export_to_csv([], str(filename))
    assert not os.path.exists(filename)
