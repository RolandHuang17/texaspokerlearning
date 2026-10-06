// The only channel between this app and the repository's numbers.
//
// ADR-0004: the trainer consumes committed artifacts and implements no poker mathematics. Every value
// drawn here was computed by `src/pokergto/**` and written by `tools/gen_all.py`. Two consequences are
// enforced in code below: the file list comes from the synced manifest (so a new artifact shows up
// without an edit here), and each file's sha256 is checked against that manifest, so a stale
// `public/data` copy fails loudly in the console instead of quietly charting an old number.

import { MANIFEST } from "../generated/manifest";

export type Locale = "zh" | "en";

export interface LangString {
  zh: string;
  en: string;
}

export interface ColumnDef {
  key: string;
  header: LangString;
  unit: string;
  digits?: number;
}

export interface Provenance {
  kind: string;
  verified: boolean;
  note?: LangString;
  source?: string;
}

export interface TableArtifact {
  id: string;
  lesson?: string;
  title: LangString;
  caption?: LangString;
  columns: ColumnDef[];
  rows: Record<string, string | number | boolean | null | LangString>[];
  source?: { module: string; function?: string | null; generator: string };
  provenance: Provenance;
  checks?: { kind: string; pass: boolean; detail?: string }[];
}

export interface RangeArtifact {
  id: string;
  lesson?: string;
  title: LangString;
  caption?: LangString;
  rows: string[];
  columns: string[];
  orientation: string;
  weights: Record<string, number>;
  cell_combos: Record<string, number>;
  range_percentage: number;
  total_combos: number;
  provenance: Provenance;
}

export interface SolverArtifact {
  id: string;
  game: string;
  algorithm: string;
  iterations: number;
  game_description: LangString;
  exploitability_bb_per_hand: number;
  exploitability_threshold: number;
  game_value_bb_per_hand: number;
  closed_form_value?: number;
  curve: { iteration: number; exploitability: number }[];
  average_strategy: Record<string, Record<string, number>>;
  checks: { kind: string; pass: boolean; value?: number; threshold?: number; detail?: string }[];
  provenance: Provenance;
}

export interface ManifestInfo {
  schemaVersion: string;
  engineVersion: string;
  artifactCount: number;
}

export const SUPPORTED_SCHEMA = "1.0.0";

const BASE = import.meta.env.BASE_URL as string;

// `MANIFEST` is generated with `as const`, so its keys are literal types; indexing it with a runtime
// path needs this widening, and nothing else about the shape changes.
const FILES = MANIFEST.files as Record<string, string>;

/**
 * Artifact paths grouped by directory, read off the synced manifest rather than a hand-kept list.
 *
 * The suffix matters: a solver run ships a JSON strategy *and* a CSV curve, and the CSV is a log for
 * the docs, not something `JSON.parse` may attempt. Callers name the shape they can consume.
 */
export function artifactsIn(directory: string, suffix = ".json"): string[] {
  const prefix = `${directory}/`;
  return Object.keys(FILES)
    .filter((name) => name.startsWith(prefix) && name.endsWith(suffix))
    .sort();
}

export function manifestInfo(): ManifestInfo {
  return {
    schemaVersion: MANIFEST.schema_version,
    engineVersion: MANIFEST.engine_version,
    artifactCount: MANIFEST.artifact_count,
  };
}

async function sha256(text: string): Promise<string> {
  const buffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function loadArtifact<T>(relative: string): Promise<T> {
  const expected: string | undefined = FILES[relative];
  if (!expected) {
    throw new Error(
      `${relative} is not listed in the synced manifest. Run \`python tools/sync_trainer_data.py\`.`,
    );
  }
  const response = await fetch(`${BASE}data/${relative}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`data/gen/${relative} could not be fetched (${response.status})`);
  }
  const text = await response.text();
  const digest = await sha256(text);
  if (digest !== expected) {
    throw new Error(
      `version skew in ${relative}: the bundle digest is ${digest.slice(0, 12)} but data/gen says ` +
        `${expected.slice(0, 12)}. Rebuild after tools/sync_trainer_data.py.`,
    );
  }
  return JSON.parse(text) as T;
}

export function pick(text: LangString | string | undefined, locale: Locale): string {
  if (text === undefined) return "";
  return typeof text === "string" ? text : text[locale];
}

/**
 * Format one cell for display. This is presentation, not mathematics: the value itself arrives from the
 * artifact, and the unit and digit count arrive from its column definition, so both languages and both
 * frontends render the same number the same way (ADR-0001).
 */
export function formatCell(
  value: string | number | boolean | null | LangString,
  column: ColumnDef,
  locale: Locale,
): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "boolean") return locale === "zh" ? (value ? "是" : "否") : value ? "yes" : "no";
  if (typeof value === "string") return value;
  if (typeof value === "object") return pick(value, locale);
  const digits = column.digits ?? 2;
  switch (column.unit) {
    case "probability":
      return `${(value * 100).toFixed(digits)}%`;
    case "percent":
      return `${value.toFixed(digits)}%`;
    case "ratio":
      return `${value.toFixed(digits)}:1`;
    default:
      return value.toFixed(digits);
  }
}

/** The five frequency bands the lessons and `src/pokergto/render.py` both use for a 13x13 cell. */
export function bandOf(frequency: number): string {
  if (frequency <= 0) return "empty";
  if (frequency < 0.01) return "trace";
  if (frequency < 0.34) return "low";
  if (frequency < 0.67) return "mid";
  if (frequency < 0.9) return "high";
  return "full";
}
