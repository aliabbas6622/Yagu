import csv
import json
from typing import List
from product_idea_miner.config.models import IdeaRecord

def export_to_json(ideas: List[IdeaRecord], filename: str):
    """
    Exports a list of IdeaRecords to a JSON file.
    """
    data = [idea.model_dump() for idea in ideas]
    # Handle datetime serialization
    def datetime_handler(x):
        if hasattr(x, 'isoformat'):
            return x.isoformat()
        raise TypeError("Unknown type")

    with open(filename, 'w') as f:
        json.dump(data, f, default=datetime_handler, indent=2)
    print(f"Exported {len(ideas)} ideas to {filename}")

def export_to_csv(ideas: List[IdeaRecord], filename: str):
    """
    Exports a list of IdeaRecords to a CSV file.
    """
    if not ideas:
        return

    headers = [
        "source", "original_url", "post_title", "problem_summary",
        "total_score", "category", "target_audience", "date_found"
    ]

    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for idea in ideas:
            row = {
                "source": idea.source.value,
                "original_url": idea.original_url,
                "post_title": idea.post_title,
                "problem_summary": idea.problem_summary,
                "total_score": idea.total_score,
                "category": idea.category,
                "target_audience": idea.target_audience,
                "date_found": idea.date_found.isoformat()
            }
            writer.writerow(row)
    print(f"Exported {len(ideas)} ideas to {filename}")
