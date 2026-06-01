import pytest
from datetime import datetime
from pydantic import ValidationError
from product_idea_miner.config.models import Source, RawPost, ProductIdea, IdeaRecord, PipelineState

def test_raw_post_model():
    post = RawPost(
        source=Source.REDDIT,
        url="https://test.com",
        title="Test Title",
        body="Test Body",
        upvotes=10
    )
    assert post.source == Source.REDDIT
    assert post.upvotes == 10
    assert post.num_comments == 0

def test_product_idea_model():
    idea = ProductIdea(
        idea="Test Idea",
        type="SaaS",
        description="A test description"
    )
    assert idea.type == "SaaS"

def test_idea_record_model():
    record = IdeaRecord(
        source=Source.HN,
        original_url="https://test.com/hn",
        post_title="HN Title",
        post_body="HN Body",
        problem_summary="Problem",
        urgency_score=10,
        frequency_score=10,
        monetization_score=10,
        total_score=30,
        product_ideas=[ProductIdea(idea="Idea", type="SaaS", description="Desc")],
        category="Category",
        target_audience="Audience",
        date_found=datetime.now()
    )
    assert record.total_score == 30
    assert len(record.product_ideas) == 1

def test_pipeline_state_model():
    state = PipelineState()
    assert state.raw_posts == []
    assert state.saved_count == 0

def test_invalid_source():
    with pytest.raises(ValidationError):
        RawPost(
            source="invalid_source",
            url="https://test.com",
            title="Title",
            body="Body"
        )
