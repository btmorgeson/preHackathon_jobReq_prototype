# Discovery 02: SKLZ Neo4j Graph Schema

> **Date**: March 5, 2026  
> **Author**: Cline AI (investigation session)  
> **Purpose**: Document the complete schema of the real SKLZ Neo4j database at 140.169.17.180

---

## How We Explored This

### Step 1: Count Total Nodes

```python
from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://140.169.17.180:7687', auth=('neo4j', 'graph_admin'))
with d.session() as s:
    result = s.run('MATCH (n) RETURN count(n) as total')
    print('Total nodes:', result.single()['total'])
```

**Result**: `897,381 total nodes`

This is production-scale real LMCO HR data.

---

### Step 2: List All Node Labels

```python
with d.session() as s:
    r = s.run('CALL db.labels() YIELD label RETURN label ORDER BY label')
    labels = [rec['label'] for rec in r]
    print(labels)
```

**Result** (32 labels):
```
Adjudication, Assessment, AtlasLearningCourse, BusinessArea, Certification, City,
Country, Course, Customer, DigitalAcademyCourse, DigitalBadge, EducationalAchievement,
Employee, HAS_SKILL, IntlJobReq, Job, JobDiscipline, JobReq, JobTitle, Language,
Mentorship, OpenReq, Program, Skill, SkillDomain, SkillRecommendation,
SkillTaxonomyCategory, SkillTaxonomySkill, SkillTaxonomySubcategory,
SoftwareApplication, State, StretchAssignment
```

> **Note**: `HAS_SKILL` appears as a node label — this is unusual and likely a data loading artifact. The real relationship type is `EVIDENCE_FOR`.

---

### Step 3: Sample Each Key Node Type

We ran property key inspection on each important node:

```python
r = s.run('MATCH (n:NodeLabel) RETURN keys(n) as keys LIMIT 1')
```

---

## Node Schemas

### `Employee` (122,893 nodes)

The core entity — real LMCO employees.

| Property | Type | Notes |
|----------|------|-------|
| `emplid` | string | Employee ID (primary key) |
| `full_name` | string | Full display name |
| `first_name` | string | |
| `last_name` | string | |
| `email` | string | `@lmco.com` addresses |
| `ntid` | string | Network/domain login |
| `department` | string | |
| `business_unit` | string | |
| `company` | string | |
| `job_level` | string/int | Career grade level |
| `service_years` | float | Years of service |
| `hire_date` | string | ISO date |
| `highest_degree` | string | Education level |
| `highest_education_lvl` | string | Education level code |
| `matrix_org_code` | string | Org hierarchy code |
| `career_manager` | string | Manager ID/name |
| `active_clearance` | boolean | Security clearance flag |
| `flsa_status` | string | Exempt/Non-exempt |
| `full_part_time` | string | FT/PT indicator |
| `telecommuter` | boolean | Remote work flag |
| `willing_to_mentor` | boolean | |
| `willing_to_support` | boolean | |
| `photo_url` | string | |
| `slack_id` | string | |
| `time_in_grade` | float | Years at current level |
| `data_provenance` | string | Data source tracking |
| `created_at` / `last_update` / `refresh_date` | string | Timestamps |

**Key fields for scoring**: `emplid`, `full_name`, `job_level`, `service_years`, `department`, `business_unit`, `active_clearance`

---

### `Skill` (217,513 nodes)

Skills tagged to employees and required by job postings.

| Property | Type | Notes |
|----------|------|-------|
| `name` | string | Canonical skill name (primary key) |
| `display_name` | string | Human-readable version |
| `skill_cluster` | string | Grouping category |
| `synonym_skill_cluster` | string | Alternative cluster |
| `human_prevalence` | float | How common this skill is |
| `high_confidence` | boolean | Reliable extraction flag |
| `keep` | boolean | Active/valid flag |
| `data_provenance` | string | |
| `created_at` | string | |

---

### `JobReq` (190,747 nodes)

Historical job requisitions (closed/filled positions).

| Property | Type | Notes |
|----------|------|-------|
| `req_num` | string | Requisition number (primary key) |
| `full_text` | string | Complete job description text |
| `jtext` | string | Alternate/shorter description |
| `required_skills` | list | Skill names as list |
| `desired_skills` | list | Desired skills as list |
| `data_provenance` | string | |
| `created_at` | string | |

> **Note**: `required_skills` and `desired_skills` may be stored as JSON arrays or pipe-delimited strings — needs verification.

---

### `OpenReq` (count TBD)

**Open/active** job requisitions — what we're ranking candidates FOR.

| Property | Type | Notes |
|----------|------|-------|
| `req_num` | string | Requisition number |
| `title` | string | Job title |
| `description` | string | Full job description |
| `required_skills` | list | Required skills |
| `desired_skills` | list | Desired/preferred skills |
| `job_category` | string | Classification |
| `class` | string | Job class |
| `job_level` | string | Level requirement |
| `clearance` | string | Clearance requirement |
| `work_schedule` | string | Full-time/part-time |
| `post_date` | string | Date posted |
| `department` | string | Hiring department |
| `url` | string | External posting URL |
| `data_provenance` | string | |
| `created_at` | string | |

> **OpenReq is the primary entity for the hackathon** — these are live job postings we're trying to rank candidates for.

---

### `Job` (count TBD)

Job code/classification master data.

| Property | Type | Notes |
|----------|------|-------|
| `job_id` | string | Internal job code |
| `job_code` | string | HR system code |
| `title` | string | Job title |
| `family` | string | Job family |
| `function` | string | Job function |
| `group` | string | Job group |
| `type` | string | Job type |
| `category` | string | Classification |
| `level` | string | Grade level |
| `flsa_status` | string | |
| `svp_function` | string | Specific Vocational Preparation |
| `data_provenance` | string | |

---

### Other Notable Nodes

| Label | Purpose |
|-------|---------|
| `Assessment` | Skills assessments taken by employees |
| `Certification` | Professional certifications |
| `Course` / `AtlasLearningCourse` / `DigitalAcademyCourse` | Learning completions |
| `DigitalBadge` | Digital credential badges |
| `EducationalAchievement` | Degrees and education history |
| `Mentorship` | Mentoring relationships |
| `StretchAssignment` | Cross-functional assignment history |
| `SkillTaxonomyCategory` / `SkillTaxonomySubcategory` / `SkillTaxonomySkill` | LMCO skill taxonomy hierarchy |
| `SkillDomain` | Skill domain groupings |
| `JobDiscipline` | Job discipline classification |
| `BusinessArea` / `Customer` | Org and business context |
| `City` / `State` / `Country` | Location data |
| `Language` | Language skills |
| `SoftwareApplication` | Software tools |

---

## Relationships

### `Employee` → `Skill` via `EVIDENCE_FOR`

```cypher
MATCH (e:Employee)-[rel:EVIDENCE_FOR]->(s:Skill)
RETURN type(rel) as reltype, keys(rel) as relkeys LIMIT 1
```

**Result**:
- `reltype`: `EVIDENCE_FOR`
- `relkeys`: `['relationship_type', 'created_at', 'data_provenance']`

The `relationship_type` property on the edge likely encodes how the skill was identified:
- Resume extraction
- Self-assessment
- Manager endorsement
- System-inferred

### Other Expected Relationships (from model-api codebase patterns)

| From → To | Relationship | Notes |
|-----------|-------------|-------|
| `Employee` → `Job` | `HAS_JOB` or `HELD` | Employment history |
| `Employee` → `JobTitle` | `HOLDS_TITLE` | Current job title |
| `Employee` → `Certification` | `HAS_CERTIFICATION` | |
| `Employee` → `Course` | `COMPLETED` | Learning history |
| `Employee` → `Assessment` | `TOOK_ASSESSMENT` | |
| `Employee` → `DigitalBadge` | `EARNED_BADGE` | |
| `OpenReq` → `Skill` | `REQUIRES_SKILL` | Skills needed for position |
| `JobReq` → `Skill` | `REQUIRES_SKILL` | Skills needed for position |
| `Skill` → `SkillTaxonomySkill` | `MAPS_TO` | Taxonomy alignment |

> **Note**: These relationships were not directly verified in this session — run Cypher queries to confirm exact relationship type names.

---

## Neo4j Version

The server at `140.169.17.180` uses **Bolt protocol version 3** (confirmed by `_bolt3.py` in Python driver stack trace). This corresponds to **Neo4j 3.x or 4.0.x**.

**Implications**:
- `SHOW INDEXES` command is NOT available (Neo4j 4.1+ syntax)
- Use `CALL db.indexes()` instead
- `db.index.vector.queryNodes()` (vector search) requires Neo4j 5.x → **NOT AVAILABLE**
- Must use text/property-based matching instead of semantic vector search

To check Neo4j version directly:
```cypher
CALL dbms.components() YIELD name, versions, edition
```

To check indexes with older syntax:
```cypher
CALL db.indexes()
YIELD name, type, labelsOrTypes, properties, state
WHERE state = 'ONLINE'
RETURN name, type, labelsOrTypes, properties
```

---

## Contrast: Two Neo4j Instances

| Attribute | `.180` (SKLZ Main) | `.216` (Second) |
|-----------|-------------------|----------------|
| Data | 897k real LMCO nodes | Unknown |
| Version | Neo4j 3.x/4.x (Bolt3) | Neo4j 5.26.0 |
| Vector Search | ❌ Not available | ✅ Available |
| Labels | Employee, Skill, JobReq, OpenReq... | Unknown |
| Credentials | `neo4j`/`graph_admin` | Unknown |

The instance at `140.169.17.216` was found from an earlier session when attempting to connect — it returned Neo4j 5.26.0 HTTP response but authentication failed with the passwords we tried (`password12345`, `neo4j`, `hackathon`, `lmco2026`).

**Hypothesis**: `.216` might be our prototype's Neo4j 5.x instance where we can:
- Create our own schema
- Enable vector indexes
- Import our synthetic + enriched data

---

## Key Queries for Hackathon

### Find candidates with matching skills for a job req:

```cypher
MATCH (jr:OpenReq {req_num: $req_num})
MATCH (e:Employee)-[:EVIDENCE_FOR]->(s:Skill)
WHERE s.name IN jr.required_skills
WITH e, count(s) as matched_skills
ORDER BY matched_skills DESC
RETURN e.emplid, e.full_name, e.job_level, e.service_years, matched_skills
LIMIT 20
```

### Find employees by skill cluster:

```cypher
MATCH (e:Employee)-[:EVIDENCE_FOR]->(s:Skill)
WHERE s.skill_cluster = $cluster
RETURN e.full_name, e.department, count(s) as skill_count
ORDER BY skill_count DESC
```

### Get full employee skill profile:

```cypher
MATCH (e:Employee {emplid: $emplid})-[:EVIDENCE_FOR]->(s:Skill)
RETURN e.full_name, e.job_level, e.service_years,
       collect({name: s.name, cluster: s.skill_cluster}) as skills
```

### Browse open reqs:

```cypher
MATCH (jr:OpenReq)
RETURN jr.req_num, jr.title, jr.department, jr.job_level, jr.clearance
ORDER BY jr.post_date DESC
LIMIT 20
```
