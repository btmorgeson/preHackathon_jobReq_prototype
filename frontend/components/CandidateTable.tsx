"use client";

import { Fragment, useMemo, useState } from "react";
import {
  SortingState,
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";

export interface CandidateResult {
  person_stable_id: string;
  name: string;
  current_title: string;
  composite_score: number;
  skill_score: number;
  role_score: number;
  experience_score: number;
  evidence: string;
  matched_skills: string[];
}

interface CandidateTableProps {
  candidates: CandidateResult[];
  selectedCandidateId?: string | null;
  onCandidateSelect?: (candidate: CandidateResult) => void;
}

const columnHelper = createColumnHelper<CandidateResult & { rank: number }>();

const scoreCell = (value: number) => value.toFixed(2);

const columns = [
  columnHelper.accessor("rank", {
    header: "Rank",
    cell: (info) => info.getValue(),
    enableSorting: false,
  }),
  columnHelper.accessor("name", {
    header: "Name",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("current_title", {
    header: "Current Title",
    cell: (info) => info.getValue(),
  }),
  columnHelper.accessor("composite_score", {
    header: "Composite",
    cell: (info) => scoreCell(info.getValue()),
  }),
  columnHelper.accessor("skill_score", {
    header: "Skill",
    cell: (info) => scoreCell(info.getValue()),
  }),
  columnHelper.accessor("role_score", {
    header: "Role",
    cell: (info) => scoreCell(info.getValue()),
  }),
  columnHelper.accessor("experience_score", {
    header: "Exp",
    cell: (info) => scoreCell(info.getValue()),
  }),
  columnHelper.accessor("matched_skills", {
    header: "Matched Skills",
    cell: (info) => {
      const skills = info.getValue();
      if (skills.length === 0) {
        return <span className="text-xs text-[var(--ink-600)]">No direct skill hits</span>;
      }
      return (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skillName, index) => (
            <span
              key={`${skillName}-${index}`}
              className="rounded-full border border-[#8ecfe2] bg-[#e8f8fe] px-2 py-0.5 text-xs font-semibold text-[#0f5771]"
            >
              {skillName}
            </span>
          ))}
        </div>
      );
    },
    enableSorting: false,
  }),
];

export default function CandidateTable({
  candidates,
  selectedCandidateId,
  onCandidateSelect,
}: CandidateTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const data = useMemo(
    () => candidates.map((candidate, index) => ({ ...candidate, rank: index + 1 })),
    [candidates],
  );

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const toggleRow = (candidate: CandidateResult) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(candidate.person_stable_id)) {
        next.delete(candidate.person_stable_id);
      } else {
        next.add(candidate.person_stable_id);
      }
      return next;
    });
    onCandidateSelect?.(candidate);
  };

  return (
    <div className="panel-surface-strong overflow-hidden">
      <div className="flex items-center justify-between border-b border-[var(--line-200)] px-4 py-3 md:px-5">
        <h3 className="text-base font-semibold text-[var(--ink-900)]">Ranked Candidates</h3>
        <span className="rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs font-semibold text-[var(--accent-600)]">
          {candidates.length} returned
        </span>
      </div>
      <div className="max-h-[560px] overflow-auto">
        <table className="min-w-[980px] text-sm leading-relaxed">
          <thead className="sticky top-0 z-10 bg-[#edf4fb]">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sorted = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      onClick={header.column.getToggleSortingHandler()}
                      className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-[0.1em] text-[var(--ink-600)] ${
                        header.column.getCanSort()
                          ? "cursor-pointer select-none transition-colors hover:bg-[#dceaf8]"
                          : ""
                      }`}
                    >
                      <span className="inline-flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {header.column.getCanSort() && (
                          <span className="text-[10px] text-[var(--ink-600)]">
                            {sorted === "asc" ? "▲" : sorted === "desc" ? "▼" : "⇵"}
                          </span>
                        )}
                      </span>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-[var(--line-200)] bg-[rgba(255,255,255,0.92)]">
            {table.getRowModel().rows.map((row) => {
              const candidate = row.original;
              const isExpanded = expandedRows.has(candidate.person_stable_id);
              const isSelected = selectedCandidateId === candidate.person_stable_id;
              return (
                <Fragment key={candidate.person_stable_id}>
                  <tr
                    onClick={() => toggleRow(candidate)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-[#d9f3fb]" : "hover:bg-[#f4f9fe]"
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3 align-top text-[var(--ink-900)]">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                  {isExpanded && (
                    <tr className="bg-[#f3f9ff]">
                      <td colSpan={columns.length} className="px-5 py-4 text-sm text-[var(--ink-700)]">
                        <span className="mb-1 block text-xs font-semibold uppercase tracking-[0.14em] text-[var(--ink-600)]">
                          Evidence
                        </span>
                        {candidate.evidence || "No evidence text available."}
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
