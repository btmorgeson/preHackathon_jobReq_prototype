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
      ? "border-[#62c2df] bg-[#e5f8fd] text-[#0f5069]"
      : "border-[#b8cadd] bg-[#f3f7fb] text-[var(--ink-700)]";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold md:text-sm ${colorClass}`}
    >
      {skill}
      <button
        onClick={onRemove}
        className="rounded-full px-1 text-base leading-none transition-opacity hover:opacity-65"
        aria-label={`Remove ${skill}`}
        type="button"
      >
        &times;
      </button>
    </span>
  );
}

function SkillInput({
  onAdd,
  placeholder,
  disabled,
}: {
  onAdd: (skill: string) => void;
  placeholder: string;
  disabled?: boolean;
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
    <div className="flex flex-col gap-2 md:flex-row">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleAdd()}
        placeholder={placeholder}
        className="h-10 flex-1 rounded-xl border border-[var(--line-300)] bg-white px-3 text-sm text-[var(--ink-900)] shadow-sm transition-colors placeholder:text-[var(--ink-600)] focus:border-[var(--accent-500)] focus:outline-none"
        disabled={disabled}
      />
      <button
        onClick={handleAdd}
        className="h-10 rounded-xl border border-transparent bg-[var(--accent-500)] px-4 text-sm font-semibold text-white transition-colors hover:bg-[var(--accent-600)] disabled:cursor-not-allowed disabled:bg-[var(--line-300)]"
        disabled={disabled}
        type="button"
      >
        Add
      </button>
    </div>
  );
}

function SkillGroup({
  title,
  caption,
  skills,
  variant,
  onRemove,
  onAdd,
}: {
  title: string;
  caption: string;
  skills: string[];
  variant: "required" | "desired";
  onRemove: (index: number) => void;
  onAdd: (skill: string) => void;
}) {
  return (
    <div className="rounded-2xl border border-[var(--line-200)] bg-[rgba(255,255,255,0.85)] px-4 py-4 shadow-sm">
      <div className="mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-[var(--ink-600)]">{title}</h3>
        <p className="mt-1 text-sm text-[var(--ink-700)]">{caption}</p>
      </div>
      <div className="mb-3 flex min-h-9 flex-wrap gap-2">
        {skills.length > 0 ? (
          skills.map((skillName, index) => (
            <SkillChip
              key={`${variant}-${skillName}-${index}`}
              skill={skillName}
              variant={variant}
              onRemove={() => onRemove(index)}
            />
          ))
        ) : (
          <p className="text-xs text-[var(--ink-600)]">No skills added yet.</p>
        )}
      </div>
      <SkillInput onAdd={onAdd} placeholder={`Add ${variant} skill...`} />
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
      <SkillGroup
        title="Required Skills"
        caption="Critical capabilities that strongly influence ranking."
        skills={requiredSkills}
        variant="required"
        onRemove={removeRequired}
        onAdd={addRequired}
      />
      <SkillGroup
        title="Desired Skills"
        caption="Secondary strengths used to break close candidate ties."
        skills={desiredSkills}
        variant="desired"
        onRemove={removeDesired}
        onAdd={addDesired}
      />
    </div>
  );
}
