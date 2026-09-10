"""Seed a local running API with a small policy document.

Run: python examples/seed.py
"""
import httpx


document = """Remote work policy

Employees may work remotely up to three days per week with their manager's approval. Core
collaboration hours are 11:00 to 16:00 India Standard Time on working days. The company reimburses
up to INR 2,000 per month for a home internet connection after submission of a receipt.
"""

response = httpx.post(
    "http://localhost:8000/v1/documents:ingest",
    json={"text": document, "source": "remote-work-policy.md", "metadata": {"department": "People"}},
    timeout=30,
)
response.raise_for_status()
print(response.json())

