"""Two-stage Graph RAG hybrid retriever.

Stage 1: Graph seed — path traversal from Posting/Skills to Person candidates.
Stage 2: Vector re-rank — filtered chunk + role vector search within the seeded pool.
Stage 3: LLM evidence — single batched Claude call for top-k candidates.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from openai import OpenAI

from src.config import get_settings
from src.graph.queries import (
    CHUNK_VECTOR_FILTERED,
    PERSON_BY_IDS,
    PERSON_CHUNK_EVIDENCE,
    POSTING_GRAPH_SEED,
    ROLE_VECTOR_FILTERED,
    SKILL_LIST_GRAPH_SEED,
)
from src.graph.schema import CHUNK_EMBEDDING_IDX, ROLE_TITLE_IDX

logger = logging.getLogger(__name__)


@dataclass
class HybridResult:
    person_stable_id: str
    name: str
    current_title: str
    graph_skill_score: float
    role_score: float
    vector_chunk_score: float
    composite_score: float
    evidence: str
    matched_skills: list[str]
    chunk_mentioned_skills: list[str] = field(default_factory=list)


def _normalize_scores(scores: dict[str, float], person_ids: list[str]) -> dict[str, float]:
    values = [scores.get(pid, 0.0) for pid in person_ids]
    if not values:
        return {}
    min_score = min(values)
    max_score = max(values)
    if max_score <= min_score:
        return {pid: 1.0 if scores.get(pid, 0.0) > 0 else 0.0 for pid in person_ids}
    scale = max_score - min_score
    return {pid: (scores.get(pid, 0.0) - min_score) / scale for pid in person_ids}


class HybridRetriever:
    def __init__(self, driver, client: OpenAI) -> None:
        self._driver = driver
        self._client = client

    def retrieve(
        self,
        query_embedding: list[float],
        posting_req_number: str | None,
        required_skills: list[str],
        desired_skills: list[str],
        weights: dict[str, float],
        top_k: int = 10,
        vector_pool_multiplier: int = 10,
        use_llm_evidence: bool = True,
    ) -> tuple[list[HybridResult], dict[str, float]]:
        """Run two-stage graph RAG and return ranked HybridResult list + timing dict."""
        timings: dict[str, float] = {}

        # --- Stage 1: Graph seed ---
        t0 = time.perf_counter()
        candidate_ids, graph_skill_scores_raw, matched_skill_names = self._stage1_graph_seed(
            posting_req_number=posting_req_number,
            required_skills=required_skills,
            desired_skills=desired_skills,
        )
        timings["graph_seed"] = (time.perf_counter() - t0) * 1000

        # Fallback: augment with global experience scores if pool is too small
        if len(candidate_ids) < top_k:
            candidate_ids, graph_skill_scores_raw, matched_skill_names = self._augment_with_global(
                query_embedding=query_embedding,
                candidate_ids=candidate_ids,
                graph_skill_scores_raw=graph_skill_scores_raw,
                matched_skill_names=matched_skill_names,
                target_size=top_k,
            )

        if not candidate_ids:
            logger.warning("No candidates found after graph seed + fallback.")
            return [], timings

        # --- Stage 2: Vector re-rank ---
        pool_size = len(candidate_ids) * vector_pool_multiplier
        t0 = time.perf_counter()
        role_scores_raw, chunk_scores_raw, chunk_mentioned = self._stage2_vector_rerank(
            query_embedding=query_embedding,
            candidate_ids=candidate_ids,
            pool_size=pool_size,
        )
        timings["vector_rerank"] = (time.perf_counter() - t0) * 1000

        # Normalize each pillar
        graph_skill_scores = _normalize_scores(graph_skill_scores_raw, candidate_ids)
        role_scores = _normalize_scores(role_scores_raw, candidate_ids)
        chunk_scores = _normalize_scores(chunk_scores_raw, candidate_ids)

        # Fetch person names/titles
        with self._driver.session() as session:
            persons = session.run(PERSON_BY_IDS, ids=candidate_ids).data()
        person_info = {r["id"]: r for r in persons}

        # Compute composite and pick top_k before generating evidence
        def composite(pid: str) -> float:
            return (
                weights["skill"] * graph_skill_scores.get(pid, 0.0)
                + weights["role"] * role_scores.get(pid, 0.0)
                + weights["experience"] * chunk_scores.get(pid, 0.0)
            )

        top_candidates = sorted(candidate_ids, key=composite, reverse=True)[:top_k]

        # --- Stage 3: LLM evidence ---
        t0 = time.perf_counter()
        if use_llm_evidence and top_candidates:
            evidence_map = self._stage3_generate_evidence(
                query_embedding=query_embedding,
                candidate_ids=top_candidates,
                posting_req_number=posting_req_number,
                required_skills=required_skills,
                person_info=person_info,
                matched_skill_names=matched_skill_names,
            )
        else:
            evidence_map = self._get_chunk_evidence(query_embedding, top_candidates)
        timings["evidence_generation"] = (time.perf_counter() - t0) * 1000

        # Assemble results
        results: list[HybridResult] = []
        for pid in top_candidates:
            info = person_info.get(pid, {})
            skill_score = graph_skill_scores.get(pid, 0.0)
            role_score = role_scores.get(pid, 0.0)
            chunk_score = chunk_scores.get(pid, 0.0)
            comp = round(
                weights["skill"] * skill_score
                + weights["role"] * role_score
                + weights["experience"] * chunk_score,
                4,
            )
            mentioned_flat = list(
                {
                    s
                    for skill_list in chunk_mentioned.get(pid, [])
                    for s in skill_list
                    if s
                }
            )
            results.append(
                HybridResult(
                    person_stable_id=pid,
                    name=info.get("name", "Unknown"),
                    current_title=info.get("current_title", ""),
                    graph_skill_score=round(skill_score, 4),
                    role_score=round(role_score, 4),
                    vector_chunk_score=round(chunk_score, 4),
                    composite_score=comp,
                    evidence=evidence_map.get(pid, ""),
                    matched_skills=matched_skill_names.get(pid, []),
                    chunk_mentioned_skills=mentioned_flat,
                )
            )

        results.sort(key=lambda r: r.composite_score, reverse=True)
        return results, timings

    # ------------------------------------------------------------------
    # Private stage methods
    # ------------------------------------------------------------------

    def _stage1_graph_seed(
        self,
        posting_req_number: str | None,
        required_skills: list[str],
        desired_skills: list[str],
    ) -> tuple[list[str], dict[str, float], dict[str, list[str]]]:
        """Graph path traversal to seed candidate pool.

        Returns (candidate_ids, raw_scores_by_id, matched_skills_by_id).
        """
        if posting_req_number:
            with self._driver.session() as session:
                records = session.run(
                    POSTING_GRAPH_SEED,
                    req_number=posting_req_number,
                ).data()
            candidate_ids = [r["person_id"] for r in records]
            raw_scores = {r["person_id"]: float(r["raw_score"]) for r in records}
            matched_skills = {r["person_id"]: r["matched_skill_names"] for r in records}
            return candidate_ids, raw_scores, matched_skills

        # Fallback: direct skill-list seed
        all_skills = required_skills + desired_skills
        if not all_skills:
            return [], {}, {}
        skill_names_lower = [s.lower() for s in all_skills]
        with self._driver.session() as session:
            records = session.run(
                SKILL_LIST_GRAPH_SEED,
                skill_names_lower=skill_names_lower,
            ).data()
        candidate_ids = [r["person_id"] for r in records]
        raw_scores = {r["person_id"]: float(r["match_count"]) for r in records}
        matched_skills = {r["person_id"]: r["matched_skill_names"] for r in records}
        return candidate_ids, raw_scores, matched_skills

    def _augment_with_global(
        self,
        query_embedding: list[float],
        candidate_ids: list[str],
        graph_skill_scores_raw: dict[str, float],
        matched_skill_names: dict[str, list[str]],
        target_size: int,
    ) -> tuple[list[str], dict[str, float], dict[str, list[str]]]:
        """Augment a small candidate pool with global chunk-vector results."""
        from src.scoring.experience_pillar import score_experience

        logger.info(
            "Graph seed returned %d candidates (< %d); augmenting with global experience search.",
            len(candidate_ids),
            target_size,
        )
        global_scores = score_experience(query_embedding, self._driver)
        existing = set(candidate_ids)
        extra_sorted = sorted(
            [pid for pid in global_scores if pid not in existing],
            key=lambda p: global_scores[p],
            reverse=True,
        )
        needed = target_size - len(candidate_ids)
        for pid in extra_sorted[:needed]:
            candidate_ids.append(pid)
            graph_skill_scores_raw[pid] = 0.0
            matched_skill_names[pid] = []
        return candidate_ids, graph_skill_scores_raw, matched_skill_names

    def _stage2_vector_rerank(
        self,
        query_embedding: list[float],
        candidate_ids: list[str],
        pool_size: int,
    ) -> tuple[dict[str, float], dict[str, float], dict[str, list[list[str]]]]:
        """Filtered vector re-rank within the candidate pool.

        Returns (role_scores_raw, chunk_scores_raw, chunk_mentioned_skills).
        chunk_mentioned_skills maps person_id -> list of skill-name lists per chunk.
        """
        # Role vector search (filtered to candidate pool)
        with self._driver.session() as session:
            role_records = session.run(
                ROLE_VECTOR_FILTERED,
                idx=ROLE_TITLE_IDX,
                top_k=pool_size,
                embedding=query_embedding,
                candidate_ids=candidate_ids,
            ).data()

        role_scores_raw: dict[str, float] = {}
        for r in role_records:
            pid = r["person_id"]
            score = float(r["score"])
            if not r.get("is_current", False):
                score *= 0.8  # recency decay for past roles
            if pid not in role_scores_raw or score > role_scores_raw[pid]:
                role_scores_raw[pid] = score

        # Chunk vector search (filtered to candidate pool + MENTIONS expansion)
        with self._driver.session() as session:
            chunk_records = session.run(
                CHUNK_VECTOR_FILTERED,
                idx=CHUNK_EMBEDDING_IDX,
                top_k=pool_size,
                embedding=query_embedding,
                candidate_ids=candidate_ids,
            ).data()

        chunk_scores_raw: dict[str, float] = {}
        chunk_mentioned_skills: dict[str, list[list[str]]] = {}
        for r in chunk_records:
            pid = r["person_id"]
            chunk_scores_raw[pid] = float(r["avg_chunk_score"])
            chunk_mentioned_skills[pid] = r["all_mentioned_skill_lists"]

        return role_scores_raw, chunk_scores_raw, chunk_mentioned_skills

    def _stage3_generate_evidence(
        self,
        query_embedding: list[float],
        candidate_ids: list[str],
        posting_req_number: str | None,
        required_skills: list[str],
        person_info: dict[str, dict],
        matched_skill_names: dict[str, list[str]],
    ) -> dict[str, str]:
        """Generate LLM evidence for top candidates via a single batched Claude call.

        Falls back to raw chunk text on any API error.
        """
        settings = get_settings()
        chunk_evidence = self._get_chunk_evidence(query_embedding, candidate_ids)

        title_part = f"REQ {posting_req_number}" if posting_req_number else "this role"
        required_str = ", ".join(required_skills) if required_skills else "general qualifications"

        candidate_blocks: list[str] = []
        for i, pid in enumerate(candidate_ids, start=1):
            info = person_info.get(pid, {})
            name = info.get("name", "Unknown")
            title = info.get("current_title", "")
            skills = ", ".join(matched_skill_names.get(pid, [])) or "none recorded"
            excerpt = (chunk_evidence.get(pid, "") or "")[:300]
            candidate_blocks.append(
                f"CANDIDATE {i}: {name}, {title}\n"
                f"Matched skills: {skills}\n"
                f"Experience excerpt: {excerpt}"
            )

        format_lines = "\n".join(
            f"CANDIDATE {i}: [justification]" for i in range(1, len(candidate_ids) + 1)
        )
        prompt = (
            f'Given the job posting for "{title_part}" requiring: {required_str}\n'
            f"For each candidate below, write a 2-3 sentence justification explaining "
            f"why they are a strong match for this role:\n\n"
            + "\n\n".join(candidate_blocks)
            + f"\n\nFormat your response as:\n{format_lines}"
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.genesis_reasoning_model,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content or ""
            return self._parse_evidence_response(response_text, candidate_ids, chunk_evidence)
        except Exception as exc:
            logger.warning(
                "LLM evidence generation failed: %s — falling back to raw chunk text.", exc
            )
            return chunk_evidence

    def _parse_evidence_response(
        self,
        response_text: str,
        candidate_ids: list[str],
        fallback: dict[str, str],
    ) -> dict[str, str]:
        """Parse batched LLM response by CANDIDATE N: markers."""
        evidence_map: dict[str, str] = {}
        for i, pid in enumerate(candidate_ids, start=1):
            marker = f"CANDIDATE {i}:"
            next_marker = f"CANDIDATE {i + 1}:"
            start_idx = response_text.find(marker)
            if start_idx == -1:
                evidence_map[pid] = fallback.get(pid, "")
                continue
            start_idx += len(marker)
            end_idx = (
                response_text.find(next_marker)
                if i < len(candidate_ids)
                else len(response_text)
            )
            evidence_map[pid] = response_text[start_idx:end_idx].strip()
        return evidence_map

    def _get_chunk_evidence(
        self,
        query_embedding: list[float],
        candidate_ids: list[str],
    ) -> dict[str, str]:
        """Get best-matching chunk text per candidate (filtered vector search)."""
        if not candidate_ids:
            return {}
        with self._driver.session() as session:
            records = session.run(
                PERSON_CHUNK_EVIDENCE,
                idx=CHUNK_EMBEDDING_IDX,
                top_k=len(candidate_ids) * 5,
                embedding=query_embedding,
                ids=candidate_ids,
            ).data()
        evidence: dict[str, str] = {}
        for r in records:
            pid = r["person_id"]
            if pid not in evidence:
                evidence[pid] = r["text"]
        return evidence
