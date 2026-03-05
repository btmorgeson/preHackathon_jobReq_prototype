"""All Cypher queries as module-level string constants."""

# Vector similarity search on role_title_idx
# Returns person_stable_id, role score, role title, top k results
ROLE_VECTOR_SEARCH = (
    "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
    "YIELD node AS role, score "
    "MATCH (p:Person)-[:HAS_ROLE]->(role) "
    "RETURN p.stable_id AS person_stable_id, score AS role_score, role.title AS role_title "
    "ORDER BY role_score DESC "
    "LIMIT $top_k"
)

# Vector similarity search on chunk_embedding_idx
# Returns person_stable_id, avg chunk score, top k results
CHUNK_VECTOR_SEARCH = (
    "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
    "YIELD node AS chunk, score "
    "MATCH (p:Person)-[:HAS_CHUNK]->(chunk) "
    "RETURN p.stable_id AS person_stable_id, avg(score) AS avg_score "
    "ORDER BY avg_score DESC "
    "LIMIT $top_k"
)

# Get all skill names for a list of person stable_ids
PERSON_SKILLS = (
    "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) "
    "WHERE p.stable_id IN $ids "
    "RETURN p.stable_id AS person_id, collect(s.name) AS skills"
)

# Get full posting by req_number
POSTING_BY_REQ_NUMBER = (
    "MATCH (po:Posting) "
    "WHERE po.req_number = $req_number "
    "RETURN po.stable_id AS stable_id, po.req_number AS req_number, "
    "       po.title AS title, po.description AS description"
)

# Get required and desired skills for a posting req_number
POSTING_REQUIRED_SKILLS = (
    "MATCH (po:Posting)-[r:REQUIRES_SKILL]->(s:Skill) "
    "WHERE po.req_number = $req_number "
    "RETURN s.name AS skill_name, r.required AS required"
)

# Get name and current_title for a list of person stable_ids
PERSON_BY_IDS = (
    "MATCH (p:Person) "
    "WHERE p.stable_id IN $ids "
    "RETURN p.stable_id AS id, p.name AS name, p.current_title AS current_title"
)
