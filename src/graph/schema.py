"""Neo4j schema constants — label and relationship type names."""

# Node labels
PERSON = "Person"
ROLE = "Role"
SKILL = "Skill"
CHUNK = "Chunk"
POSTING = "Posting"

# Relationship types
HAS_ROLE = "HAS_ROLE"
HAS_SKILL = "HAS_SKILL"
HAS_CHUNK = "HAS_CHUNK"
REQUIRES_SKILL = "REQUIRES_SKILL"

# Vector indexes
CHUNK_EMBEDDING_IDX = "chunk_embedding_idx"
ROLE_TITLE_IDX = "role_title_idx"
SKILL_NAME_FT_IDX = "skill_name_ft"
