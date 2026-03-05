"""
Smoke test against running API (localhost:8000).
7 test cases.

Usage:
    python scripts/06_smoke_test.py
    python scripts/06_smoke_test.py --base-url http://localhost:8000
"""

import argparse
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

SSL_CERT = os.environ.get("SSL_CERT_FILE", "C:/Users/e477258/combined_pem.pem")
os.environ.setdefault("SSL_CERT_FILE", SSL_CERT)
os.environ.setdefault("REQUESTS_CA_BUNDLE", SSL_CERT)

import httpx  # after env setup


def run_tests(base_url: str) -> None:
    # Use plain HTTP for localhost (no SSL needed)
    client = httpx.Client(base_url=base_url, timeout=30.0)

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

    # Test 1: Health check
    try:
        r = client.get("/")
        check("Health check GET /", r.status_code == 200 and r.json().get("status") == "ok")
    except Exception as e:
        check("Health check GET /", False, str(e))

    # Test 2: Extract skills
    try:
        r = client.post(
            "/api/extract-skills",
            json={"text": "Senior Python Engineer. Must have: Python, SQL. Nice to have: Docker, Kubernetes."},
        )
        data = r.json()
        check(
            "POST /api/extract-skills returns skills",
            r.status_code == 200
            and isinstance(data.get("required_skills"), list)
            and len(data["required_skills"]) > 0,
        )
    except Exception as e:
        check("POST /api/extract-skills returns skills", False, str(e))

    # Test 3: Search Software Engineer
    try:
        r = client.post(
            "/api/search",
            json={
                "role_title": "Software Engineer",
                "required_skills": ["Python", "SQL"],
                "desired_skills": ["Docker"],
                "top_k": 10,
            },
        )
        data = r.json()
        check(
            "POST /api/search Software Engineer returns 10 candidates",
            r.status_code == 200 and len(data.get("candidates", [])) == 10,
        )
        if r.status_code == 200 and data.get("candidates"):
            c = data["candidates"][0]
            check(
                "Candidate has valid composite_score",
                0.0 <= c["composite_score"] <= 1.0,
            )
    except Exception as e:
        check("POST /api/search Software Engineer", False, str(e))

    # Test 4: Search Program Manager (different ranking)
    try:
        r = client.post(
            "/api/search",
            json={
                "role_title": "Program Manager",
                "required_skills": ["Project Management", "Stakeholder Management"],
                "top_k": 10,
            },
        )
        data = r.json()
        check(
            "POST /api/search Program Manager returns candidates",
            r.status_code == 200 and len(data.get("candidates", [])) > 0,
        )
    except Exception as e:
        check("POST /api/search Program Manager", False, str(e))

    # Test 5: GET posting REQ-001
    try:
        r = client.get("/api/postings/REQ-001")
        data = r.json()
        check(
            "GET /api/postings/REQ-001 returns posting",
            r.status_code == 200
            and data.get("req_number") == "REQ-001"
            and isinstance(data.get("required_skills"), list),
        )
    except Exception as e:
        check("GET /api/postings/REQ-001", False, str(e))

    # Test 6: Custom weights
    try:
        r = client.post(
            "/api/search",
            json={
                "role_title": "Data Scientist",
                "weights": {"skill": 0.8, "role": 0.1, "experience": 0.1},
                "top_k": 5,
            },
        )
        check(
            "POST /api/search custom weights accepted",
            r.status_code == 200 and len(r.json().get("candidates", [])) > 0,
        )
    except Exception as e:
        check("POST /api/search custom weights", False, str(e))

    # Test 7: Empty input graceful error
    try:
        r = client.post("/api/search", json={})
        check(
            "POST /api/search empty input returns 422 or 200 with empty",
            r.status_code in (200, 422, 400),
        )
    except Exception as e:
        check("POST /api/search empty input", False, str(e))

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed > 0:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test for job req API")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()
    run_tests(args.base_url)


if __name__ == "__main__":
    main()
