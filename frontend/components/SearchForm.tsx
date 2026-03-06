"use client";

import { useMemo, useState } from "react";

import { API_URL } from "@/lib/apiConfig";
import SkillEditor from "./SkillEditor";

export interface SearchWeights {
  skill: number;
  role: number;
  experience: number;
}

export interface QueryContext {
  posting_title?: string;
  posting_description?: string;
}

export interface SearchRequest {
  req_number?: string;
  role_title?: string;
  role_description?: string;
  query_context?: QueryContext;
  required_skills: string[];
  desired_skills: string[];
  weights?: SearchWeights;
  top_k?: number;
}

interface ReqLookupResult {
  stable_id: string;
  req_number: string;
  title: string;
  description: string;
  required_skills: string[];
  desired_skills: string[];
}

interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

type Tab = "req" | "description";

function uniqueSkills(values: string[]): string[] {
  const seen = new Set<string>();
  const normalized: string[] = [];
  values.forEach((value) => {
    const trimmed = value.trim();
    const key = trimmed.toLowerCase();
    if (!trimmed || seen.has(key)) {
      return;
    }
    seen.add(key);
    normalized.push(trimmed);
  });
  return normalized;
}

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [activeTab, setActiveTab] = useState<Tab>("req");
  const [reqNumber, setReqNumber] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState<string[]>([]);
  const [desiredSkills, setDesiredSkills] = useState<string[]>([]);
  const [postingContext, setPostingContext] = useState<QueryContext | null>(null);
  const [fetchingReq, setFetchingReq] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const hasIntent = useMemo(() => {
    const hasSkills = requiredSkills.length > 0 || desiredSkills.length > 0;
    if (activeTab === "req") {
      return reqNumber.trim().length > 0 || hasSkills;
    }
    return description.trim().length > 0 || hasSkills;
  }, [activeTab, description, desiredSkills.length, reqNumber, requiredSkills.length]);

  const isBusy = fetchingReq || isLoading;
  const canSearch = hasIntent && !isBusy;

  const handleSkillUpdate = (required: string[], desired: string[]) => {
    setRequiredSkills(uniqueSkills(required));
    setDesiredSkills(uniqueSkills(desired));
  };

  const handleReqLookup = async () => {
    if (!reqNumber.trim() || isLoading) {
      return;
    }
    setFetchingReq(true);
    setFetchError(null);
    try {
      const res = await fetch(`${API_URL}/api/postings/${encodeURIComponent(reqNumber.trim())}`);
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data: ReqLookupResult = await res.json();
      setRequiredSkills(uniqueSkills(data.required_skills ?? []));
      setDesiredSkills(uniqueSkills(data.desired_skills ?? []));
      setPostingContext({
        posting_title: data.title,
        posting_description: data.description,
      });
    } catch (err) {
      setPostingContext(null);
      setFetchError(err instanceof Error ? err.message : "Failed to fetch requisition.");
    } finally {
      setFetchingReq(false);
    }
  };

  const handleExtractSkills = async () => {
    if (!description.trim() || isLoading) {
      return;
    }
    setFetchingReq(true);
    setFetchError(null);
    try {
      const res = await fetch(`${API_URL}/api/extract-skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: description }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(`HTTP ${res.status}: ${detail}`);
      }
      const data = await res.json();
      setRequiredSkills(uniqueSkills(data.required_skills ?? []));
      setDesiredSkills(uniqueSkills(data.desired_skills ?? []));
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to extract skills.");
    } finally {
      setFetchingReq(false);
    }
  };

  const handleSearch = () => {
    if (!canSearch) {
      return;
    }
    const request: SearchRequest = {
      required_skills: uniqueSkills(requiredSkills),
      desired_skills: uniqueSkills(desiredSkills),
      top_k: 10,
    };
    if (activeTab === "req" && reqNumber.trim()) {
      request.req_number = reqNumber.trim();
      if (postingContext) {
        request.query_context = postingContext;
      }
    } else if (activeTab === "description" && description.trim()) {
      request.role_description = description.trim();
    }
    onSearch(request);
  };

  return (
    <section className="panel-surface px-5 py-6 md:px-7 md:py-7">
      <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <h2 className="text-xl font-semibold text-[var(--ink-900)]">Search Setup</h2>
          <p className="text-sm text-[var(--ink-700)]">
            Start from a requisition or a freeform role description, then refine required and desired skills.
          </p>
        </div>
        <div className="inline-flex w-full rounded-full border border-[var(--line-200)] bg-white p-1 md:w-auto">
          <button
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "req"
                ? "bg-[var(--accent-500)] text-white shadow-sm"
                : "text-[var(--ink-700)] hover:bg-[var(--accent-soft)]"
            }`}
            onClick={() => {
              setFetchError(null);
              setActiveTab("req");
            }}
            type="button"
          >
            Req Number
          </button>
          <button
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              activeTab === "description"
                ? "bg-[var(--accent-500)] text-white shadow-sm"
                : "text-[var(--ink-700)] hover:bg-[var(--accent-soft)]"
            }`}
            onClick={() => {
              setFetchError(null);
              setActiveTab("description");
            }}
            type="button"
          >
            Role Description
          </button>
        </div>
      </div>

      {activeTab === "req" ? (
        <div className="space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--ink-600)]">
            Requisition Lookup
          </label>
          <div className="flex flex-col gap-2 md:flex-row">
            <input
              type="text"
              value={reqNumber}
              onChange={(e) => {
                setReqNumber(e.target.value);
                setPostingContext(null);
              }}
              onKeyDown={(e) => e.key === "Enter" && handleReqLookup()}
              placeholder="e.g. REQ-001"
              className="h-11 flex-1 rounded-xl border border-[var(--line-300)] bg-white px-3.5 text-sm text-[var(--ink-900)] shadow-sm transition-colors placeholder:text-[var(--ink-600)] focus:border-[var(--accent-500)] focus:outline-none"
              disabled={isBusy}
            />
            <button
              onClick={handleReqLookup}
              disabled={fetchingReq || !reqNumber.trim() || isLoading}
              className="h-11 rounded-xl border border-transparent bg-[var(--ink-900)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#0d1d2e] disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
            >
              {fetchingReq ? "Loading Req..." : "Load Req"}
            </button>
          </div>
          {postingContext?.posting_title && (
            <p className="rounded-lg bg-[var(--accent-soft)] px-3 py-2 text-sm text-[var(--ink-700)]">
              Loaded context: <span className="font-semibold text-[var(--ink-900)]">{postingContext.posting_title}</span>
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <label className="block text-xs font-semibold uppercase tracking-[0.18em] text-[var(--ink-600)]">
            Description Parsing
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste the job description text here..."
            rows={5}
            className="w-full rounded-xl border border-[var(--line-300)] bg-white px-3.5 py-2.5 text-sm text-[var(--ink-900)] shadow-sm transition-colors placeholder:text-[var(--ink-600)] focus:border-[var(--accent-500)] focus:outline-none"
            disabled={isBusy}
          />
          <button
            onClick={handleExtractSkills}
            disabled={fetchingReq || !description.trim() || isLoading}
            className="h-10 rounded-xl border border-transparent bg-[var(--ink-900)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#0d1d2e] disabled:cursor-not-allowed disabled:opacity-60"
            type="button"
          >
            {fetchingReq ? "Extracting Skills..." : "Extract Skills"}
          </button>
        </div>
      )}

      {fetchError && (
        <p className="mt-4 rounded-lg border border-[var(--danger-500)] bg-[var(--danger-soft)] px-3 py-2 text-sm text-[var(--danger-500)]">
          {fetchError}
        </p>
      )}

      <div className="mt-5">
        <SkillEditor
          requiredSkills={requiredSkills}
          desiredSkills={desiredSkills}
          onUpdate={handleSkillUpdate}
        />
      </div>

      <button
        onClick={handleSearch}
        disabled={!canSearch}
        className="mt-6 inline-flex h-11 w-full items-center justify-center rounded-xl border border-transparent bg-[var(--accent-500)] px-4 text-base font-semibold text-white transition-colors hover:bg-[var(--accent-600)] disabled:cursor-not-allowed disabled:bg-[var(--line-300)]"
        type="button"
      >
        {isLoading ? "Running Search..." : fetchingReq ? "Wait for skill sync..." : "Find Candidates"}
      </button>
    </section>
  );
}
