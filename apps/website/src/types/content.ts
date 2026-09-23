import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  to: string;
}
export interface Step {
  number: string;
  title: string;
  description: string;
}
export interface Capability {
  icon: LucideIcon;
  title: string;
  bullets: string[];
}
export interface Metric {
  value: string;
  label: string;
  detail: string;
}
export interface FaqItem {
  question: string;
  answer: string;
}
export interface Tool {
  name: string;
  purpose: string;
  params: string;
  returns: string;
}
export interface Guardrail {
  icon: LucideIcon;
  title: string;
  description: string;
}
export interface TraceStep {
  tool: string;
  args: string;
  status: 'ok' | 'error' | 'rejected';
  ms: number;
  note?: string;
}
export interface CodeSample {
  title: string;
  language: string;
  code: string;
}
