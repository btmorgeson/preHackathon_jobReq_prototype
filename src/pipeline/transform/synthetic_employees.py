"""
Synthetic employee generator.

Produces 500 Person records with roles, skills, and text chunks,
plus 10 job posting records. Outputs to Parquet files.
"""

import logging
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

from src.pipeline.transform.normalize import make_stable_id

logger = logging.getLogger(__name__)

NUM_PERSONS = 500
NUM_POSTINGS = 10
OUTPUT_DIR = Path("data/parquet")

fake = Faker()
Faker.seed(42)
random.seed(42)

POSTING_TITLES = [
    "Software Engineer II",
    "Senior Systems Analyst",
    "Data Scientist",
    "Program Manager",
    "Cybersecurity Engineer",
    "Cloud Infrastructure Engineer",
    "Machine Learning Engineer",
    "Systems Integration Engineer",
    "DevSecOps Engineer",
    "Technical Project Lead",
]

POSTING_DESCRIPTIONS = [
    "Design and develop robust software systems supporting mission-critical applications.",
    "Analyze complex system requirements and translate them into technical specifications.",
    "Build and deploy ML models to extract insights from large-scale sensor datasets.",
    "Lead cross-functional teams to deliver high-visibility programs on schedule.",
    "Assess and harden systems against cyber threats using NIST RMF frameworks.",
    "Architect and manage cloud-native infrastructure across hybrid environments.",
    "Research and implement novel ML algorithms for advanced analytics pipelines.",
    "Integrate heterogeneous systems using modern middleware and API frameworks.",
    "Implement security-as-code practices across CI/CD pipelines and infrastructure.",
    "Drive technical execution for multi-phase engineering development programs.",
]


def _random_date(start_year: int = 2010, end_year: int = 2022) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def _make_summary_chunk(person_stable_id: str, name: str, current_title: str, activities: list[str]) -> dict:
    acts = random.sample(activities, min(3, len(activities)))
    text = (
        f"{name} is an experienced professional currently serving as {current_title}. "
        f"Key areas of focus include: {'; '.join(acts).lower()}. "
        f"Brings a track record of delivering results in fast-paced, collaborative environments."
    )
    return {
        "stable_id": make_stable_id("chunk", f"{person_stable_id}|summary"),
        "person_stable_id": person_stable_id,
        "text": text,
        "chunk_type": "summary",
    }


def _make_closeout_chunks(person_stable_id: str, name: str, roles: list[dict], skills: list[str]) -> list[dict]:
    chunks = []
    num_chunks = random.randint(1, 3)
    verbs = ["Led", "Developed", "Designed", "Implemented", "Delivered", "Managed", "Architected", "Built"]
    outcomes = [
        "resulting in 30% efficiency improvement",
        "reducing system downtime by 40%",
        "enabling real-time data processing at scale",
        "achieving on-time delivery within budget",
        "improving team velocity by 25%",
        "earning recognition from senior leadership",
        "successfully passing DoD accreditation review",
        "supporting a $50M program milestone",
    ]
    for i in range(num_chunks):
        verb = random.choice(verbs)
        skill = random.choice(skills) if skills else "cross-functional collaboration"
        role = random.choice(roles)
        outcome = random.choice(outcomes)
        text = (
            f"{verb} a {skill}-focused initiative as {role['title']}, {outcome}. "
            f"Coordinated with stakeholders across engineering, operations, and program management."
        )
        chunks.append({
            "stable_id": make_stable_id("chunk", f"{person_stable_id}|closeout|{i}"),
            "person_stable_id": person_stable_id,
            "text": text,
            "chunk_type": "closeout",
        })
    return chunks


def generate(onet_data: dict, output_dir: Path = OUTPUT_DIR) -> dict[str, pd.DataFrame]:
    """
    Generate synthetic employee data and job postings. Returns dict of DataFrames.
    Also writes Parquet files to output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    occupations = onet_data["occupations"]
    skills_by_soc = onet_data["skills_by_soc"]
    activities_by_soc = onet_data["activities_by_soc"]
    all_activities = onet_data.get("all_activities", [])

    persons_rows = []
    roles_rows = []
    skills_rows = {}  # name -> stable_id
    person_skills_rows = []
    chunks_rows = []

    for i in range(NUM_PERSONS):
        person_stable_id = make_stable_id("person", str(i))
        name = fake.name()
        employee_id = f"EMP{10000 + i}"

        # Assign 1-4 roles
        num_roles = random.randint(1, 4)
        chosen_occs = random.choices(occupations, k=num_roles)

        roles_for_person = []
        current_start = _random_date(2018, 2023)
        for j, occ in enumerate(chosen_occs):
            is_current = (j == num_roles - 1)
            role_start = _random_date(2010 + j * 2, 2014 + j * 2)
            role_end = None if is_current else role_start + timedelta(days=random.randint(365, 1095))
            role = {
                "stable_id": make_stable_id("role", f"{person_stable_id}|{j}"),
                "person_stable_id": person_stable_id,
                "title": occ["title"],
                "soc_code": occ["soc_code"],
                "start_date": role_start.isoformat(),
                "end_date": role_end.isoformat() if role_end else None,
                "is_current": is_current,
            }
            roles_for_person.append(role)
            roles_rows.append(role)

        current_occ = chosen_occs[-1]
        current_title = current_occ["title"]
        current_soc = current_occ["soc_code"]

        persons_rows.append({
            "stable_id": person_stable_id,
            "name": name,
            "employee_id": employee_id,
            "current_title": current_title,
        })

        # Assign 8-15 skills from primary occupation
        candidate_skills = skills_by_soc.get(current_soc, []) or list(onet_data.get("all_skills", []))
        if not candidate_skills:
            candidate_skills = ["Communication", "Problem Solving", "Teamwork"]
        num_skills = random.randint(8, min(15, len(candidate_skills)))
        person_skill_names = random.sample(candidate_skills, num_skills)

        for skill_name in person_skill_names:
            if skill_name not in skills_rows:
                skills_rows[skill_name] = make_stable_id("skill", skill_name)
            person_skills_rows.append({
                "person_stable_id": person_stable_id,
                "skill_stable_id": skills_rows[skill_name],
            })

        # Summary chunk
        activities = activities_by_soc.get(current_soc, all_activities) or all_activities
        if not activities:
            activities = ["delivering mission-critical solutions", "collaborating with stakeholders"]
        summary = _make_summary_chunk(person_stable_id, name, current_title, activities)
        chunks_rows.append(summary)

        # 1-3 closeout chunks
        closeouts = _make_closeout_chunks(person_stable_id, name, roles_for_person, person_skill_names)
        chunks_rows.extend(closeouts)

    # Build skills DataFrame (unique skills)
    skills_df = pd.DataFrame([
        {"stable_id": sid, "name": name}
        for name, sid in skills_rows.items()
    ])

    # Build postings
    postings_rows = []
    all_skill_names = list(skills_rows.keys())
    for k in range(NUM_POSTINGS):
        req_num = f"REQ-{k+1:03d}"
        title = POSTING_TITLES[k]
        desc = POSTING_DESCRIPTIONS[k]
        required = random.sample(all_skill_names, min(5, len(all_skill_names)))
        desired = random.sample([s for s in all_skill_names if s not in required], min(4, len(all_skill_names) - len(required)))
        postings_rows.append({
            "stable_id": make_stable_id("posting", req_num),
            "req_number": req_num,
            "title": title,
            "description": desc,
            "required_skills": required,
            "desired_skills": desired,
        })

    dfs = {
        "persons": pd.DataFrame(persons_rows),
        "roles": pd.DataFrame(roles_rows),
        "skills": skills_df,
        "person_skills": pd.DataFrame(person_skills_rows),
        "chunks": pd.DataFrame(chunks_rows),
        "postings": pd.DataFrame(postings_rows),
    }

    # Write parquet — postings has list columns, use object dtype
    for name, df in dfs.items():
        path = output_dir / f"{name}.parquet"
        df.to_parquet(path, index=False)
        logger.info("Wrote %s (%d rows) → %s", name, len(df), path)

    return dfs
