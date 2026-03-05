"use client";

import { useState } from "react";
import SearchForm, { SearchRequest } from "@/components/SearchForm";
import CandidateTable, { CandidateResult } from "@/components/CandidateTable";
import ScoreBreakdown from "@/components/ScoreBreakdown";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [results, setResults] = useState<CandidateResult[] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] =
    useState<CandidateResult | null>(null);

  const handleSearch = async (request: SearchRequest) => {
    setIsLoading(true);
    setError(null);
    setResults(null);
    setSelectedCandidate(null);
    try {
      const res = await fetch(`${API_URL}/api/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data = await res.json();
      const candidates: CandidateResult[] = data.candidates ?? [];
      setResults(candidates);
      if (candidates.length > 0) {
        setSelectedCandidate(candidates[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-7xl mx-auto space-y-6">
        <header>
          <h1 className="text-2xl font-bold text-gray-900">
            Job Req Candidate Ranker
          </h1>
          <p className="text-sm text-gray-500">HR AI Hackathon Prototype</p>
        </header>

        <SearchForm onSearch={handleSearch} isLoading={isLoading} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {results !== null && (
          <>
            <p className="text-sm text-gray-600">
              {results.length} candidate{results.length !== 1 ? "s" : ""} found.
              Click a row to expand evidence.
            </p>
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1 min-w-0">
                <CandidateTable candidates={results} />
              </div>
              <div className="lg:w-72 shrink-0">
                <ScoreBreakdown candidate={selectedCandidate} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
