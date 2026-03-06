"use client";

import { useMemo, useState } from "react";

import CandidateTable, { CandidateResult } from "@/components/CandidateTable";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import SearchForm, { SearchRequest } from "@/components/SearchForm";
import { API_URL } from "@/lib/apiConfig";

interface SearchResponse {
  request_id: string;
  candidates: CandidateResult[];
  query_skills_used: string[];
  timings_ms: Record<string, number>;
}

type UiPhase = "idle" | "loading" | "error" | "success";

function snapshotRequest(request: SearchRequest): SearchRequest {
  return {
    ...request,
    required_skills: [...request.required_skills],
    desired_skills: [...request.desired_skills],
    query_context: request.query_context ? { ...request.query_context } : undefined,
    weights: request.weights ? { ...request.weights } : undefined,
  };
}

export default function Home() {
  const [results, setResults] = useState<CandidateResult[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [phase, setPhase] = useState<UiPhase>("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastRequest, setLastRequest] = useState<SearchRequest | null>(null);
  const [lastResponse, setLastResponse] = useState<SearchResponse | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateResult | null>(null);

  const runSearch = async (request: SearchRequest) => {
    const requestSnapshot = snapshotRequest(request);
    setIsLoading(true);
    setPhase("loading");
    setError(null);
    setResults(null);
    setSelectedCandidate(null);
    setLastResponse(null);
    setLastRequest(requestSnapshot);
    try {
      const res = await fetch(`${API_URL}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestSnapshot),
      });
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const payload = await res.json();
          detail = payload?.error?.message || detail;
        } catch {
          // Keep status fallback when response is not valid JSON.
        }
        throw new Error(detail);
      }
      const data: SearchResponse = await res.json();
      const candidates = data.candidates ?? [];
      setLastResponse(data);
      setResults(candidates);
      setPhase("success");
      if (candidates.length > 0) {
        setSelectedCandidate(candidates[0]);
      }
    } catch (err) {
      setLastResponse(null);
      setPhase("error");
      setError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const querySummary = useMemo(() => {
    if (!lastRequest) {
      return null;
    }
    return {
      req: lastRequest.req_number || "-",
      title: lastRequest.query_context?.posting_title || lastRequest.role_title || "-",
      requiredCount: lastRequest.required_skills.length,
      desiredCount: lastRequest.desired_skills.length,
      weights: lastRequest.weights || { skill: 0.4, role: 0.3, experience: 0.3 },
    };
  }, [lastRequest]);

  return (
    <main className="min-h-screen px-4 py-8 md:px-7 lg:px-10">
      <div className="mx-auto max-w-[1280px] space-y-6">
        <header className="panel-surface muted-grid reveal px-6 py-7 md:px-8 md:py-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--ink-600)]">
                Talent Intelligence Studio
              </p>
              <h1 className="text-3xl font-bold text-[var(--ink-900)] md:text-4xl">
                Job Req Candidate Ranker
              </h1>
              <p className="max-w-2xl text-sm text-[var(--ink-700)] md:text-base">
                Evaluate candidate fit across skills, role progression, and experience vectors with a
                calibrated scoring model built for fast hiring decisions.
              </p>
            </div>
            <div className="grid w-full max-w-sm gap-3 rounded-2xl border border-[var(--line-200)] bg-[rgba(255,255,255,0.82)] px-4 py-4 text-sm text-[var(--ink-700)] shadow-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-[var(--ink-600)]">Status</span>
                <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-semibold text-[var(--accent-600)]">
                  {phase.toUpperCase()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium text-[var(--ink-600)]">Selected Candidate</span>
                <span className="truncate pl-3 text-right font-semibold text-[var(--ink-900)]">
                  {selectedCandidate?.name ?? "None"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-medium text-[var(--ink-600)]">Last Request</span>
                <span className="truncate pl-3 text-right font-semibold text-[var(--ink-900)]">
                  {lastResponse?.request_id.slice(0, 8) ?? "Not run"}
                </span>
              </div>
            </div>
          </div>
        </header>

        <section className="reveal reveal-delay-1">
          <SearchForm onSearch={runSearch} isLoading={isLoading} />
        </section>

        {querySummary && (
          <section className="panel-surface reveal reveal-delay-2 px-5 py-4 text-sm text-[var(--ink-700)] md:px-6 md:py-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--ink-600)]">
              Query Summary
            </p>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              <p>
                <span className="block text-xs font-medium text-[var(--ink-600)]">Req</span>
                <span className="font-semibold text-[var(--ink-900)]">{querySummary.req}</span>
              </p>
              <p className="md:col-span-1 xl:col-span-2">
                <span className="block text-xs font-medium text-[var(--ink-600)]">Context Title</span>
                <span className="font-semibold text-[var(--ink-900)]">{querySummary.title}</span>
              </p>
              <p>
                <span className="block text-xs font-medium text-[var(--ink-600)]">Required / Desired</span>
                <span className="font-semibold text-[var(--ink-900)]">
                  {querySummary.requiredCount} / {querySummary.desiredCount}
                </span>
              </p>
              <p className="xl:col-span-2">
                <span className="block text-xs font-medium text-[var(--ink-600)]">Weights</span>
                <span className="font-semibold text-[var(--ink-900)]">
                  skill={querySummary.weights.skill}, role={querySummary.weights.role}, experience=
                  {querySummary.weights.experience}
                </span>
              </p>
            </div>
            {lastResponse && (
              <p className="mt-3 text-xs text-[var(--ink-600)]">
                Request ID: <span className="font-semibold text-[var(--ink-900)]">{lastResponse.request_id}</span>
                {" · "}
                Total ms:{" "}
                <span className="font-semibold text-[var(--ink-900)]">
                  {lastResponse.timings_ms.request_total ?? "-"}
                </span>
              </p>
            )}
          </section>
        )}

        {phase === "loading" && (
          <div className="panel-surface px-5 py-4 text-sm font-medium text-[var(--ink-700)]">
            Running candidate search and scoring pipeline...
          </div>
        )}

        {error && (
          <div className="panel-surface flex flex-col gap-3 border-[var(--danger-500)] bg-[var(--danger-soft)] px-5 py-4 text-sm text-[var(--danger-500)] md:flex-row md:items-center md:justify-between">
            <span>{error}</span>
            <button
              className="inline-flex w-fit items-center justify-center rounded-full bg-[var(--danger-500)] px-4 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-[#a73e3e] disabled:cursor-not-allowed disabled:opacity-60"
              onClick={() => lastRequest && runSearch(lastRequest)}
              disabled={!lastRequest || isLoading}
            >
              Retry Search
            </button>
          </div>
        )}

        {results !== null && results.length === 0 && (
          <div className="panel-surface px-5 py-4 text-sm text-[var(--ink-700)]">
            No candidates matched this query. Try broadening required skills or adding a few desired skills.
          </div>
        )}

        {results !== null && results.length > 0 && (
          <section className="space-y-4">
            <p className="text-sm font-medium text-[var(--ink-700)]">
              {results.length} candidate{results.length !== 1 ? "s" : ""} found. Select a row to inspect detailed
              evidence.
            </p>
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
              <div className="min-w-0">
                <CandidateTable
                  candidates={results}
                  selectedCandidateId={selectedCandidate?.person_stable_id ?? null}
                  onCandidateSelect={setSelectedCandidate}
                />
              </div>
              <div className="xl:sticky xl:top-6 xl:h-fit">
                <ScoreBreakdown candidate={selectedCandidate} />
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
