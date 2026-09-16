"use client";

import type { components } from "@/types/api";

type SubmissionState = components["schemas"]["SubmissionState"];

const LABEL: Record<SubmissionState, string> = {
  submitted: "已提交",
  grading: "批改中",
  graded: "已批改",
};

const TONE: Record<SubmissionState, string> = {
  submitted: "",
  grading: "warn",
  graded: "ok",
};

export function StateTag({ state }: { state: SubmissionState }) {
  return <span className={`tag ${TONE[state]}`}>{LABEL[state]}</span>;
}
