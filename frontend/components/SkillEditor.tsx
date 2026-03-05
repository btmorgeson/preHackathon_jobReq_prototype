"use client";

import { useState } from "react";

interface SkillEditorProps {
  requiredSkills: string[];
  desiredSkills: string[];
  onUpdate: (required: string[], desired: string[]) => void;
}

function SkillChip({
  skill,
  variant,
  onRemove,
}: {
  skill: string;
  variant: "required" | "desired";
  onRemove: () => void;
}) {
  const colorClass =
    variant === "required"
      ? "bg-blue-100 text-blue-800 border-blue-300"
      : "bg-gray-100 text-gray-700 border-gray-300";

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-sm font-medium ${colorClass}`}
    >
      {skill}
      <button
        onClick={onRemove}
        className="ml-1 hover:opacity-70 leading-none"
        aria-label={`Remove ${skill}`}
      >
        &times;
      </button>
    </span>
  );
}

function SkillInput({
  onAdd,
  placeholder,
}: {
  onAdd: (skill: string) => void;
  placeholder: string;
}) {
  const [value, setValue] = useState("");

  const handleAdd = () => {
    const trimmed = value.trim();
    if (trimmed) {
      onAdd(trimmed);
      setValue("");
    }
  };

  return (
    <div className="flex gap-2 mt-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        placeholder={placeholder}
        className="flex-1 border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      <button
        onClick={handleAdd}
        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
      >
        Add
      </button>
    </div>
  );
}

export default function SkillEditor({
  requiredSkills,
  desiredSkills,
  onUpdate,
}: SkillEditorProps) {
  const removeRequired = (idx: number) => {
    const updated = requiredSkills.filter((_, i) => i !== idx);
    onUpdate(updated, desiredSkills);
  };

  const removeDesired = (idx: number) => {
    const updated = desiredSkills.filter((_, i) => i !== idx);
    onUpdate(requiredSkills, updated);
  };

  const addRequired = (skill: string) => {
    onUpdate([...requiredSkills, skill], desiredSkills);
  };

  const addDesired = (skill: string) => {
    onUpdate(requiredSkills, [...desiredSkills, skill]);
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-1">
          Required Skills
        </h3>
        <div className="flex flex-wrap gap-2 min-h-8">
          {requiredSkills.map((s, i) => (
            <SkillChip
              key={`req-${i}`}
              skill={s}
              variant="required"
              onRemove={() => removeRequired(i)}
            />
          ))}
        </div>
        <SkillInput onAdd={addRequired} placeholder="Add required skill..." />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-1">
          Desired Skills
        </h3>
        <div className="flex flex-wrap gap-2 min-h-8">
          {desiredSkills.map((s, i) => (
            <SkillChip
              key={`des-${i}`}
              skill={s}
              variant="desired"
              onRemove={() => removeDesired(i)}
            />
          ))}
        </div>
        <SkillInput onAdd={addDesired} placeholder="Add desired skill..." />
      </div>
    </div>
  );
}
