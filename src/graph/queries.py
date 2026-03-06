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

# Graph-seed: Posting -> REQUIRES_SKILL -> Skill <- HAS_SKILL <- Person
# Returns person_id, matched_skill_names, raw_score (required skills score 2, desired score 1)
POSTING_GRAPH_SEED = (
    "MATCH (po:Posting)-[r:REQUIRES_SKILL]->(s:Skill)<-[:HAS_SKILL]-(p:Person) "
    "WHERE po.req_number = $req_number "
    "WITH p.stable_id AS person_id, "
    "     collect(DISTINCT s.name) AS matched_skill_names, "
    "     sum(CASE WHEN r.required THEN 2 ELSE 1 END) AS raw_score "
    "RETURN person_id, matched_skill_names, raw_score "
    "ORDER BY raw_score DESC"
)

# Graph-seed fallback: skill list (when no req_number available)
# Returns person_id, matched_skill_names, match_count
SKILL_LIST_GRAPH_SEED = (
    "MATCH (p:Person)-[:HAS_SKILL]->(s:Skill) "
    "WHERE toLower(s.name) IN $skill_names_lower "
    "WITH p.stable_id AS person_id, "
    "     collect(DISTINCT s.name) AS matched_skill_names, "
    "     count(DISTINCT s) AS match_count "
    "RETURN person_id, matched_skill_names, match_count "
    "ORDER BY match_count DESC"
)

# Filtered chunk vector search + MENTIONS graph expansion (constrained to candidate pool)
# WHERE must come after YIELD — cannot pre-filter a vector index CALL
CHUNK_VECTOR_FILTERED = (
    "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
    "YIELD node AS chunk, score "
    "MATCH (p:Person)-[:HAS_CHUNK]->(chunk) "
    "WHERE p.stable_id IN $candidate_ids "
    "OPTIONAL MATCH (chunk)-[:MENTIONS]->(s:Skill) "
    "WITH p.stable_id AS person_id, chunk, score, collect(s.name) AS mentioned_skills "
    "RETURN person_id, avg(score) AS avg_chunk_score, "
    "       collect(mentioned_skills) AS all_mentioned_skill_lists "
    "ORDER BY avg_chunk_score DESC"
)

# Filtered role vector search (constrained to candidate pool)
ROLE_VECTOR_FILTERED = (
    "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
    "YIELD node AS role, score "
    "MATCH (p:Person)-[:HAS_ROLE]->(role) "
    "WHERE p.stable_id IN $candidate_ids "
    "RETURN p.stable_id AS person_id, role.is_current AS is_current, "
    "       role.start_date AS start_date, score "
    "ORDER BY person_id, is_current DESC, start_date DESC"
)

# Best chunk per candidate for evidence generation (filtered vector search)
PERSON_CHUNK_EVIDENCE = (
    "CALL db.index.vector.queryNodes($idx, $top_k, $embedding) "
    "YIELD node AS chunk, score "
    "MATCH (p:Person)-[:HAS_CHUNK]->(chunk) "
    "WHERE p.stable_id IN $ids "
    "RETURN p.stable_id AS person_id, chunk.text AS text, score "
    "ORDER BY score DESC"
)
