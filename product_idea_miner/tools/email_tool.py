import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List
from product_idea_miner.config.models import IdeaRecord
from product_idea_miner.config.settings import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    RECIPIENT_EMAIL
)

def send_digest_email(ideas: List[IdeaRecord], recipient: str = RECIPIENT_EMAIL) -> bool:
    """
    Sends an HTML email digest of product ideas.
    """
    if not ideas:
        print("No ideas to send in digest.")
        return False

    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, recipient]):
        print("Email configuration incomplete. Skipping digest email.")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"🧠 {len(ideas)} Fresh Product Ideas — {today}"

    html = f"""
    <html>
    <head>
        <style>
            .card {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 20px;
                font-family: sans-serif;
            }}
            .header {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
            .meta {{ font-size: 14px; color: #7f8c8d; margin-top: 4px; }}
            .score {{ color: #e67e22; font-weight: bold; }}
            .ideas {{ margin-top: 12px; }}
            .idea-item {{ margin-bottom: 8px; }}
            .idea-name {{ font-weight: bold; }}
            .btn {{
                display: inline-block;
                padding: 8px 16px;
                background-color: #3498db;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin-top: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>Daily Product Idea Digest</h1>
        <p>Here are the top pain points and product ideas discovered today:</p>
    """

    for i, idea in enumerate(ideas, 1):
        product_ideas_html = "".join([
            f"<div class='idea-item'><span class='idea-name'>→ {p.idea} ({p.type}):</span> {p.description}</div>"
            for p in idea.product_ideas
        ])

        html += f"""
        <div class="card">
            <div class="header">#{i} — {idea.problem_summary}</div>
            <div class="meta">
                Source: {idea.source} | <span class="score">Score: {idea.total_score}/30</span><br>
                Category: {idea.category} | Target: {idea.target_audience}
            </div>
            <div class="ideas">
                <strong>Product Ideas:</strong>
                {product_ideas_html}
            </div>
            <a href="{idea.original_url}" class="btn">View Original Post ↗</a>
        </div>
        """

    html += """
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = recipient

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Digest email sent successfully to {recipient}")
        return True
    except Exception as e:
        print(f"Failed to send digest email: {e}")
        return False
