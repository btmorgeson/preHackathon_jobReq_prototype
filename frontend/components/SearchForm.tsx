"use client";

import { useState } from "react";
import SkillEditor from "./SkillEditor";

export interface SearchRequest {
  role_title?: string;
  role_description?: string;
  required_skills: string[];
  desired_skills: string[];
  weights?: { skill: number; role: number; experience: number };
  top_k?: number;
}

interface SearchFormProps {
  onSearch: (request: SearchRequest) => void;
  isLoading: boolean;
}

type Tab = "req" | "description";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SearchForm({ onSearch, isLoading }: SearchFormProps) {
  const [activeTab, setActiveTab] = useState<Tab>("req");
  const [reqNumber, setReqNumber] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState<string[]>([]);
  const [desiredSkills, setDesiredSkills] = useState<string[]>([]);
  const [fetchingReq, setFetchingReq] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const handleSkillUpdate = (required: string[], desired: string[]) => {
    setRequiredSkills(required);
    setDesiredSkills(desired);
  };

  const handleReqLookup = async () => {
    if (!reqNumber.trim()) return;
    setFetchingReq(true);
    setFetchError(null);
    try {
      const res = await fetch(`${API_URL}/api/postings/${encodeURIComponent(reqNumber.trim())}`);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setRequiredSkills(data.required_skills ?? []);
      setDesiredSkills(data.desired_skills ?? []);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to fetch req");
    } finally {
      setFetchingReq(false);
    }
  };

  const handleExtractSkills = async () => {
    if (!description.trim()) return;
    setFetchingReq(true);
    setFetchError(null);
    try {
      const res = await fetch(`${API_URL}/api/extract-skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: description }),
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setRequiredSkills(data.required_skills ?? []);
      setDesiredSkills(data.desired_skills ?? []);
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : "Failed to extract skills");
    } finally {
      setFetchingReq(false);
    }
  };

  const handleSearch = () => {
    const request: SearchRequest = {
      required_skills: requiredSkills,
      desired_skills: desiredSkills,
      top_k: 10,
    };
    if (activeTab === "req" && reqNumber.trim()) {
      request.role_title = reqNumber.trim();
    } else if (activeTab === "description" && description.trim()) {
      request.role_description = description.trim();
    }
    onSearch(request);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <div className="flex border-b border-gray-200">
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            activeTab === "req"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("req")}
        >
          Req Number
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            activeTab === "description"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
          onClick={() => setActiveTab("description")}
        >
          Role Description
        </button>
      </div>

      {activeTab === "req" ? (
        <div className="flex gap-2">
          <input
            type="text"
            value={reqNumber}
            onChange={(e) => setReqNumber(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleReqLookup()}
            placeholder="e.g. REQ-001"
            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
          <button
            onClick={handleReqLookup}
            disabled={fetchingReq || !reqNumber.trim()}
            className="px-4 py-2 bg-gray-700 text-white text-sm rounded hover:bg-gray-800 disabled:opacity-50"
          >
            {fetchingReq ? "Loading..." : "Load Req"}
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste job description here..."
            rows={4}
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 resize-none"
          />
          <button
            onClick={handleExtractSkills}
            disabled={fetchingReq || !description.trim()}
            className="px-4 py-2 bg-gray-700 text-white text-sm rounded hover:bg-gray-800 disabled:opacity-50"
          >
            {fetchingReq ? "Extracting..." : "Extract Skills"}
          </button>
        </div>
      )}

      {fetchError && (
        <p className="text-red-600 text-sm">{fetchError}</p>
      )}

      <SkillEditor
        requiredSkills={requiredSkills}
        desiredSkills={desiredSkills}
        onUpdate={handleSkillUpdate}
      />

      <button
        onClick={handleSearch}
        disabled={isLoading || (requiredSkills.length === 0 && desiredSkills.length === 0)}
        className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {isLoading ? "Searching..." : "Find Candidates"}
      </button>
    </div>
  );
}
