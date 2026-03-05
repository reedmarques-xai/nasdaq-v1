"use client";
import { useState } from "react";
import type { XSource } from "@/lib/types";

export default function XSourcesPanel({ sources }: { sources: XSource[] }) {
  const [open, setOpen] = useState(false);
  if (!sources.length) return null;

  return (
    <div className="mt-4">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 w-full text-left bg-bg border border-border rounded-lg px-4 py-3 text-sm font-semibold hover:bg-blue-bg/30 transition-colors"
      >
        <span className="text-base">𝕏</span>
        X Sources
        <span className="ml-auto text-blue text-xs font-normal">
          {sources.length} post{sources.length !== 1 ? "s" : ""}
        </span>
        <span className={`text-text-muted transition-transform ${open ? "rotate-180" : ""}`}>▼</span>
      </button>

      {open && (
        <div className="bg-bg border border-border border-t-0 rounded-b-lg max-h-80 overflow-y-auto">
          {sources.map((src, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2 text-xs hover:bg-blue/5 transition-colors">
              <span className="text-blue font-semibold min-w-[100px]">{src.display_label}</span>
              <a href={src.url} target="_blank" rel="noopener" className="text-text-muted hover:text-blue hover:underline truncate">
                {src.url}
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
