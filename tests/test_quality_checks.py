import pandas as pd

from src.pipeline.quality_checks import assert_generated_dataframes


def test_assert_generated_dataframes_accepts_valid_data() -> None:
    persons = pd.DataFrame(
        [
            {"stable_id": "p1", "name": "A", "employee_id": "EMP1", "current_title": "Engineer"},
            {"stable_id": "p2", "name": "B", "employee_id": "EMP2", "current_title": "Analyst"},
        ]
    )
    roles = pd.DataFrame(
        [
            {
                "stable_id": "r1",
                "person_stable_id": "p1",
                "title": "Engineer",
                "soc_code": "15-1252.00",
                "start_date": "2020-01-01",
                "end_date": None,
                "is_current": True,
            }
        ]
    )
    skills = pd.DataFrame([{"stable_id": "s1", "name": "Python"}])
    person_skills = pd.DataFrame([{"person_stable_id": "p1", "skill_stable_id": "s1"}])
    chunks = pd.DataFrame(
        [
            {
                "stable_id": "c1",
                "person_stable_id": "p1",
                "text": "Worked on Python systems",
                "chunk_type": "summary",
            }
        ]
    )
    postings = pd.DataFrame(
        [
            {
                "stable_id": "po1",
                "req_number": "REQ-001",
                "title": "Engineer",
                "description": "Build systems",
                "required_skills": ["Python"],
                "desired_skills": [],
            }
        ]
    )
    dfs = {
        "persons": persons,
        "roles": roles,
        "skills": skills,
        "person_skills": person_skills,
        "chunks": chunks,
        "postings": postings,
    }
    assert_generated_dataframes(dfs)
