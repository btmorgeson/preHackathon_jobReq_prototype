"use client";

import { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
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
}

const columnHelper = createColumnHelper<CandidateResult & { rank: number }>();

const scoreCell = (value: number) => value.toFixed(3);

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
      return (
        <div className="flex flex-wrap gap-1">
          {skills.map((s, i) => (
            <span
              key={i}
              className="px-1.5 py-0.5 bg-green-100 text-green-800 text-xs rounded"
            >
              {s}
            </span>
          ))}
        </div>
      );
    },
    enableSorting: false,
  }),
];

export default function CandidateTable({ candidates }: CandidateTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const data = candidates.map((c, i) => ({ ...c, rank: i + 1 }));

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className={`px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap ${
                    header.column.getCanSort()
                      ? "cursor-pointer select-none hover:bg-gray-100"
                      : ""
                  }`}
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getCanSort() && (
                    <span className="ml-1">
                      {header.column.getIsSorted() === "asc"
                        ? " ^"
                        : header.column.getIsSorted() === "desc"
                        ? " v"
                        : " -"}
                    </span>
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {table.getRowModel().rows.map((row) => {
            const isExpanded = expandedRows.has(row.id);
            return (
              <>
                <tr
                  key={row.id}
                  onClick={() => toggleRow(row.id)}
                  className="hover:bg-gray-50 cursor-pointer"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-3 py-2">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {isExpanded && (
                  <tr key={`${row.id}-evidence`} className="bg-blue-50">
                    <td
                      colSpan={columns.length}
                      className="px-4 py-3 text-xs text-gray-700"
                    >
                      <span className="font-semibold">Evidence: </span>
                      {row.original.evidence}
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
