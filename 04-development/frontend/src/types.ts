// 与后端 schemas.py 对应的前端类型
export interface Basics {
  name: string;
  phone: string;
  email: string;
  location: string;
  title: string;
}
export interface ExperienceItem {
  company: string;
  role: string;
  period: string;
  bullets: string[];
}
export interface ProjectItem {
  name: string;
  role: string;
  period: string;
  bullets: string[];
}
export interface Education {
  school: string;
  major: string;
  degree: string;
  period: string;
}
export interface ResumeStructured {
  basics: Basics;
  summary: string;
  education: Education[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  skills: string[];
}
export interface DiffItem {
  section: string;
  original: string;
  polished: string;
  reason: string;
}
export interface PolishResult {
  resume: ResumeStructured;
  diffs: DiffItem[];
}

export type Intent = "polish" | "target" | "grammar";

// 状态机：对应 PRD 的多轮状态流转
export type AppState =
  | "IDLE"
  | "UPLOADING"
  | "PARSING"
  | "NEED_TARGET"
  | "POLISHING"
  | "REVIEW"
  | "EXPORTING"
  | "DONE"
  | "PARSE_FAILED"
  | "POLISH_FAILED";
