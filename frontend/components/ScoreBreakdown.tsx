"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import type { CandidateResult } from "./CandidateTable";

interface ScoreBreakdownProps {
  candidate: CandidateResult | null;
}

const SCORE_BARS = [
  { key: "skill_score", label: "Skill Score", color: "#3b82f6" },
  { key: "role_score", label: "Role Score", color: "#10b981" },
  { key: "experience_score", label: "Exp Score", color: "#f59e0b" },
] as const;

export default function ScoreBreakdown({ candidate }: ScoreBreakdownProps) {
  if (!candidate) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center h-48 text-gray-400 text-sm">
        Select a candidate to see score breakdown
      </div>
    );
  }

  const data = SCORE_BARS.map(({ key, label, color }) => ({
    label,
    score: candidate[key],
    color,
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-sm font-semibold text-gray-700 mb-1">
        Score Breakdown
      </h3>
      <p className="text-xs text-gray-500 mb-4">
        {candidate.name} &mdash; {candidate.current_title}
      </p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 4, right: 24, left: 8, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 1]} tickCount={6} tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="label"
            width={80}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            formatter={(value: number | string | undefined) =>
              typeof value === "number" ? value.toFixed(3) : value
            }
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
