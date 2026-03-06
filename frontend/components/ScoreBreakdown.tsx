"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CandidateResult } from "./CandidateTable";

interface ScoreBreakdownProps {
  candidate: CandidateResult | null;
}

const SCORE_BARS = [
  { key: "skill_score", label: "Skill Score", color: "#0c8db8" },
  { key: "role_score", label: "Role Score", color: "#1f6b8c" },
  { key: "experience_score", label: "Experience", color: "#2f8c74" },
] as const;

export default function ScoreBreakdown({ candidate }: ScoreBreakdownProps) {
  if (!candidate) {
    return (
      <aside className="panel-surface-strong flex min-h-60 flex-col items-center justify-center gap-2 px-6 py-6 text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.14em] text-[var(--ink-600)]">Score Breakdown</p>
        <p className="text-sm text-[var(--ink-700)]">Select a candidate row to inspect skill, role, and experience scoring.</p>
      </aside>
    );
  }

  const data = SCORE_BARS.map(({ key, label, color }) => ({
    label,
    score: candidate[key],
    color,
  }));

  return (
    <aside className="panel-surface-strong px-5 py-5 md:px-6">
      <div className="mb-4 space-y-2 border-b border-[var(--line-200)] pb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--ink-600)]">Score Breakdown</p>
        <h3 className="text-lg font-semibold text-[var(--ink-900)]">{candidate.name}</h3>
        <p className="text-sm text-[var(--ink-700)]">{candidate.current_title}</p>
        <div className="inline-flex rounded-full border border-[#8bcfe3] bg-[#e8f8fe] px-3 py-1 text-xs font-semibold text-[#0c5a76]">
          Composite {candidate.composite_score.toFixed(2)}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart layout="vertical" data={data} margin={{ top: 4, right: 14, left: 10, bottom: 6 }}>
          <CartesianGrid horizontal={false} strokeDasharray="4 4" stroke="#c6d8ea" />
          <XAxis
            type="number"
            domain={[0, 1]}
            tickCount={6}
            tick={{ fill: "#3f5f7d", fontSize: 11 }}
            axisLine={{ stroke: "#aac1d8" }}
            tickLine={{ stroke: "#aac1d8" }}
          />
          <YAxis
            type="category"
            dataKey="label"
            width={88}
            tick={{ fill: "#3f5f7d", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number | string | undefined) =>
              typeof value === "number" ? value.toFixed(3) : value
            }
            contentStyle={{
              borderRadius: 10,
              border: "1px solid #2c4f6e",
              backgroundColor: "#10263a",
              color: "#e6f3ff",
              fontSize: 12,
            }}
            labelStyle={{ color: "#b6d7ef", fontWeight: 600 }}
          />
          <Bar dataKey="score" radius={[0, 6, 6, 0]}>
            {data.map((entry, index) => (
              <Cell key={`${entry.label}-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </aside>
  );
}
