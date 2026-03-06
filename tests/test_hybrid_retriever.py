"""Unit tests for the entity linker used in MENTIONS edge creation."""

from src.pipeline.embed.embed_pipeline import _link_chunk_to_skills


def test_link_chunk_to_skills_exact_match() -> None:
    text = "Proficient in Python and experienced with SQL databases."
    skills = ["Python", "SQL", "Java"]
    result = _link_chunk_to_skills(text, skills)
    assert "Python" in result
    assert "SQL" in result
    assert "Java" not in result


def test_link_chunk_to_skills_case_insensitive() -> None:
    text = "PYTHON developer with strong JAVA background."
    skills = ["Python", "Java"]
    result = _link_chunk_to_skills(text, skills)
    assert "Python" in result
    assert "Java" in result


def test_link_chunk_to_skills_no_partial_word_match() -> None:
    # "C" skill must NOT match inside "Cloud", "CAD", "Cisco"
    text = "Worked on Cloud infrastructure with CAD tools and Cisco networking."
    skills = ["C"]
    result = _link_chunk_to_skills(text, skills)
    assert "C" not in result


def test_link_chunk_to_skills_short_skill_standalone() -> None:
    # "C" should match when it appears as a standalone word
    text = "Languages: C, Python, Java."
    skills = ["C"]
    result = _link_chunk_to_skills(text, skills)
    assert "C" in result


def test_link_chunk_to_skills_empty_text() -> None:
    result = _link_chunk_to_skills("", ["Python", "SQL"])
    assert result == []


def test_link_chunk_to_skills_empty_skills() -> None:
    result = _link_chunk_to_skills("Expert Python developer.", [])
    assert result == []


def test_link_chunk_to_skills_multi_word_skill() -> None:
    text = "Experience with machine learning and deep learning frameworks."
    skills = ["machine learning", "deep learning", "Python"]
    result = _link_chunk_to_skills(text, skills)
    assert "machine learning" in result
    assert "deep learning" in result
    assert "Python" not in result
