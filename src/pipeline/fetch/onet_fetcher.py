"""
O*NET database fetcher.

Downloads the O*NET database zip, extracts relevant TSV files, and parses
occupations, skills, and work activities into JSON files.

Falls back to a hardcoded list of 35 SOC codes if the download fails.
"""

import io
import json
import logging
import urllib.request
import zipfile
from pathlib import Path

from src.config import get_settings

logger = logging.getLogger(__name__)

ONET_ZIP_URL = "https://www.onetcenter.org/dl_files/database/db_29_2_text.zip"
RAW_DIR = Path("data/raw/onet")

FALLBACK_SOC_CODES = [
    {"soc_code": "15-1252.00", "title": "Software Developers"},
    {"soc_code": "15-1251.00", "title": "Computer Programmers"},
    {"soc_code": "15-1299.00", "title": "Computer Occupations, All Other"},
    {"soc_code": "15-1211.00", "title": "Computer Systems Analysts"},
    {"soc_code": "15-1212.00", "title": "Information Security Analysts"},
    {"soc_code": "15-1221.00", "title": "Computer and Information Research Scientists"},
    {"soc_code": "15-1231.00", "title": "Computer Network Support Specialists"},
    {"soc_code": "15-1241.00", "title": "Computer Network Architects"},
    {"soc_code": "15-1244.00", "title": "Network and Computer Systems Administrators"},
    {"soc_code": "15-2051.00", "title": "Data Scientists"},
    {"soc_code": "15-2031.00", "title": "Operations Research Analysts"},
    {"soc_code": "17-2141.00", "title": "Mechanical Engineers"},
    {"soc_code": "17-2071.00", "title": "Electrical Engineers"},
    {"soc_code": "17-2061.00", "title": "Computer Hardware Engineers"},
    {"soc_code": "17-2051.00", "title": "Civil Engineers"},
    {"soc_code": "17-2112.00", "title": "Industrial Engineers"},
    {"soc_code": "17-2199.00", "title": "Engineers, All Other"},
    {"soc_code": "11-3021.00", "title": "Computer and Information Systems Managers"},
    {"soc_code": "11-1021.00", "title": "General and Operations Managers"},
    {"soc_code": "11-9041.00", "title": "Architectural and Engineering Managers"},
    {"soc_code": "11-2021.00", "title": "Marketing Managers"},
    {"soc_code": "11-3031.00", "title": "Financial Managers"},
    {"soc_code": "11-9199.00", "title": "Managers, All Other"},
    {"soc_code": "13-1082.00", "title": "Project Management Specialists"},
    {"soc_code": "13-1111.00", "title": "Management Analysts"},
    {"soc_code": "13-1161.00", "title": "Market Research Analysts and Marketing Specialists"},
    {"soc_code": "13-2011.00", "title": "Accountants and Auditors"},
    {"soc_code": "13-1071.00", "title": "Human Resources Specialists"},
    {"soc_code": "19-1042.00", "title": "Medical Scientists, Except Epidemiologists"},
    {"soc_code": "19-2041.00", "title": "Environmental Scientists"},
    {"soc_code": "19-3011.00", "title": "Economists"},
    {"soc_code": "43-9111.00", "title": "Statistical Assistants"},
    {"soc_code": "15-1255.00", "title": "Web and Digital Interface Designers"},
    {"soc_code": "15-1256.00", "title": "Web Developers"},
    {"soc_code": "15-1257.00", "title": "Web and Digital Interface Designers"},
]

FALLBACK_SKILLS = [
    "Python", "Java", "SQL", "JavaScript", "TypeScript",
    "Data Analysis", "Machine Learning", "Project Management",
    "Cloud Computing", "AWS", "Azure", "Docker", "Kubernetes",
    "Agile", "Scrum", "Communication", "Problem Solving",
    "Git", "Linux", "Network Security", "API Development",
    "Database Design", "Statistical Analysis", "R Programming",
    "C++", "C#", ".NET", "React", "Node.js",
    "Systems Engineering", "Technical Writing", "Risk Management",
    "Requirements Analysis", "Quality Assurance", "DevOps",
    "Cybersecurity", "Data Modeling", "ETL Pipeline Development",
    "Business Analysis", "Stakeholder Management",
]

FALLBACK_WORK_ACTIVITIES = [
    "Analyzing data or information to find answers to technical problems",
    "Developing software applications and systems",
    "Collaborating with cross-functional teams to deliver projects",
    "Designing and implementing network infrastructure",
    "Documenting technical requirements and specifications",
    "Conducting security assessments and vulnerability testing",
    "Managing project timelines and deliverables",
    "Providing technical guidance and mentoring to junior staff",
    "Evaluating vendor solutions and making technology recommendations",
    "Automating workflows and processes using scripting tools",
    "Leading agile ceremonies including sprint planning and retrospectives",
    "Building and maintaining CI/CD pipelines",
    "Conducting code reviews and enforcing coding standards",
    "Researching emerging technologies and industry trends",
    "Supporting production systems and resolving incidents",
]


def _download_and_extract(output_dir: Path) -> bool:
    """Download O*NET zip and extract to output_dir. Returns True on success."""
    logger.info("Downloading O*NET database from %s", ONET_ZIP_URL)
    try:
        settings = get_settings()
        import ssl
        ctx = ssl.create_default_context(cafile=settings.ssl_cert_file)

        import urllib.request
        with urllib.request.urlopen(ONET_ZIP_URL, context=ctx, timeout=120) as resp:
            data = resp.read()

        logger.info("Downloaded %d bytes, extracting...", len(data))
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(output_dir)
        logger.info("Extracted to %s", output_dir)
        return True
    except Exception as exc:
        logger.warning("O*NET download failed: %s — using fallback data", exc)
        return False


def _find_file(base_dir: Path, filename: str) -> Path | None:
    """Find a file by name (case-insensitive) anywhere in base_dir."""
    for path in base_dir.rglob("*"):
        if path.name.lower() == filename.lower():
            return path
    return None


def _parse_occupation_data(onet_dir: Path) -> list[dict]:
    """Parse Occupation Data.txt → list of {soc_code, title}."""
    path = _find_file(onet_dir, "Occupation Data.txt")
    if not path:
        logger.warning("Occupation Data.txt not found, using fallback")
        return FALLBACK_SOC_CODES

    occupations = []
    try:
        with open(path, encoding="utf-8-sig") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue  # skip header
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 2:
                    occupations.append({"soc_code": parts[0], "title": parts[1]})
        logger.info("Parsed %d occupations", len(occupations))
        return occupations if occupations else FALLBACK_SOC_CODES
    except Exception as exc:
        logger.warning("Failed to parse Occupation Data.txt: %s", exc)
        return FALLBACK_SOC_CODES


def _parse_skills(onet_dir: Path) -> dict[str, list[str]]:
    """Parse Skills.txt → {soc_code: [skill_name, ...]}."""
    path = _find_file(onet_dir, "Skills.txt")
    if not path:
        logger.warning("Skills.txt not found, using fallback")
        return {}

    skills_by_soc: dict[str, list[str]] = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4:
                    soc = parts[0]
                    skill_name = parts[3]
                    skills_by_soc.setdefault(soc, [])
                    if skill_name and skill_name not in skills_by_soc[soc]:
                        skills_by_soc[soc].append(skill_name)
        logger.info("Parsed skills for %d SOC codes", len(skills_by_soc))
        return skills_by_soc
    except Exception as exc:
        logger.warning("Failed to parse Skills.txt: %s", exc)
        return {}


def _parse_work_activities(onet_dir: Path) -> dict[str, list[str]]:
    """Parse Work Activities.txt → {soc_code: [activity_description, ...]}."""
    path = _find_file(onet_dir, "Work Activities.txt")
    if not path:
        logger.warning("Work Activities.txt not found, using fallback")
        return {}

    activities_by_soc: dict[str, list[str]] = {}
    try:
        with open(path, encoding="utf-8-sig") as f:
            for i, line in enumerate(f):
                if i == 0:
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 4:
                    soc = parts[0]
                    activity = parts[3]
                    activities_by_soc.setdefault(soc, [])
                    if activity and activity not in activities_by_soc[soc]:
                        activities_by_soc[soc].append(activity)
        logger.info("Parsed work activities for %d SOC codes", len(activities_by_soc))
        return activities_by_soc
    except Exception as exc:
        logger.warning("Failed to parse Work Activities.txt: %s", exc)
        return {}


def fetch_onet(output_dir: Path = RAW_DIR) -> dict:
    """
    Fetch and parse O*NET data. Returns a dict with:
      - occupations: list of {soc_code, title}
      - skills_by_soc: {soc_code: [skill_name]}
      - activities_by_soc: {soc_code: [activity_description]}
      - all_skills: sorted list of unique skill names
      - all_activities: list of unique activity descriptions
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = _download_and_extract(output_dir)

    if downloaded:
        occupations = _parse_occupation_data(output_dir)
        skills_by_soc = _parse_skills(output_dir)
        activities_by_soc = _parse_work_activities(output_dir)
    else:
        occupations = FALLBACK_SOC_CODES
        skills_by_soc = {}
        activities_by_soc = {}

    # Build fallback skill mappings for SOC codes missing from O*NET
    for occ in occupations:
        soc = occ["soc_code"]
        if soc not in skills_by_soc:
            skills_by_soc[soc] = FALLBACK_SKILLS[:]
        if soc not in activities_by_soc:
            activities_by_soc[soc] = FALLBACK_WORK_ACTIVITIES[:]

    # Collect all unique skills and activities
    all_skills: set[str] = set()
    for skills in skills_by_soc.values():
        all_skills.update(skills)
    all_skills.update(FALLBACK_SKILLS)

    all_activities: list[str] = []
    seen_activities: set[str] = set()
    for acts in activities_by_soc.values():
        for a in acts:
            if a not in seen_activities:
                all_activities.append(a)
                seen_activities.add(a)
    if not all_activities:
        all_activities = FALLBACK_WORK_ACTIVITIES[:]

    result = {
        "occupations": occupations,
        "skills_by_soc": skills_by_soc,
        "activities_by_soc": activities_by_soc,
        "all_skills": sorted(all_skills),
        "all_activities": all_activities,
    }

    # Persist to JSON
    onet_json = output_dir / "onet_data.json"
    with open(onet_json, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info("Saved O*NET data to %s", onet_json)

    return result
