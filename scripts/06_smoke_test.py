"""
Smoke test against running API (default: http://localhost:8000).

Usage:
    python scripts/06_smoke_test.py
    python scripts/06_smoke_test.py --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


def run_tests(base_url: str) -> None:
    client = httpx.Client(base_url=base_url, timeout=45.0)

    passed = 0
    failed = 0

    def check(name: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}" + (f": {detail}" if detail else ""))
            failed += 1

    print(f"\nRunning smoke tests against {base_url}\n")

    # 1) Health endpoint
    try:
        response = client.get("/")
        check("GET / returns status ok", response.status_code == 200 and response.json().get("status") == "ok")
    except Exception as exc:
        check("GET / returns status ok", False, str(exc))

    # 2) req lookup
    try:
        response = client.get("/api/postings/REQ-001")
        payload = response.json()
        check(
            "GET /api/postings/REQ-001 returns required shape",
            response.status_code == 200
            and payload.get("req_number") == "REQ-001"
            and isinstance(payload.get("required_skills"), list)
            and isinstance(payload.get("desired_skills"), list),
        )
    except Exception as exc:
        check("GET /api/postings/REQ-001 returns required shape", False, str(exc))

    # 3) skill extraction
    try:
        response = client.post(
            "/api/extract-skills",
            json={"text": "Senior Python Engineer. Must have Python and SQL. Nice to have Docker."},
        )
        payload = response.json()
        check(
            "POST /api/extract-skills returns arrays",
            response.status_code == 200
            and isinstance(payload.get("required_skills"), list)
            and isinstance(payload.get("desired_skills"), list),
        )
    except Exception as exc:
        check("POST /api/extract-skills returns arrays", False, str(exc))

    # 4) search by req number + context
    try:
        posting = client.get("/api/postings/REQ-001").json()
        response = client.post(
            "/api/search",
            json={
                "req_number": "REQ-001",
                "query_context": {
                    "posting_title": posting["title"],
                    "posting_description": posting["description"],
                },
                "required_skills": posting["required_skills"],
                "desired_skills": posting["desired_skills"],
                "top_k": 10,
            },
        )
        payload = response.json()
        candidates = payload.get("candidates", [])
        check(
            "POST /api/search returns request_id and timings",
            response.status_code == 200
            and isinstance(payload.get("request_id"), str)
            and isinstance(payload.get("timings_ms"), dict),
        )
        check(
            "POST /api/search returns sorted candidate list",
            len(candidates) > 0
            and all(
                candidates[i]["composite_score"] >= candidates[i + 1]["composite_score"]
                for i in range(len(candidates) - 1)
            ),
        )
    except Exception as exc:
        check("POST /api/search req context flow", False, str(exc))

    # 5) custom weights accepted + top_k respected
    try:
        response = client.post(
            "/api/search",
            json={
                "role_title": "Data Scientist",
                "required_skills": ["Python", "SQL"],
                "desired_skills": ["Machine Learning"],
                "weights": {"skill": 0.7, "role": 0.2, "experience": 0.1},
                "top_k": 5,
            },
        )
        payload = response.json()
        check(
            "POST /api/search honors top_k",
            response.status_code == 200 and len(payload.get("candidates", [])) <= 5,
        )
    except Exception as exc:
        check("POST /api/search honors top_k", False, str(exc))

    # 6) invalid payload gets consistent error shape
    try:
        response = client.post("/api/search", json={})
        payload = response.json()
        check(
            "POST /api/search invalid payload returns error envelope",
            response.status_code == 422
            and isinstance(payload.get("error"), dict)
            and payload["error"].get("code") == "validation_error"
            and isinstance(payload["error"].get("request_id"), str),
        )
    except Exception as exc:
        check("POST /api/search invalid payload returns error envelope", False, str(exc))

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test for job req API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    run_tests(args.base_url)


if __name__ == "__main__":
    main()
