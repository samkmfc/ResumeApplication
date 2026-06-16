import { useState } from "react";
import {
  exportResume,
  parseResume,
  polishStream,
  uploadResume,
} from "./api";
import type { AppState, DiffItem, Intent, ResumeStructured } from "./types";

const STEPS: { key: AppState[]; label: string }[] = [
  { key: ["UPLOADING", "PARSING", "PARSE_FAILED"], label: "1 上传简历" },
  { key: ["NEED_TARGET"], label: "2 目标岗位" },
  { key: ["POLISHING", "POLISH_FAILED"], label: "3 AI 润色" },
  { key: ["REVIEW"], label: "4 对比采纳" },
  { key: ["EXPORTING", "DONE"], label: "5 导出下载" },
];

const INTENTS: { v: Intent; label: string }[] = [
  { v: "polish", label: "综合润色" },
  { v: "target", label: "岗位定向" },
  { v: "grammar", label: "仅语法" },
];

export default function App() {
  const [state, setState] = useState<AppState>("IDLE");
  const [error, setError] = useState("");
  const [resume, setResume] = useState<ResumeStructured | null>(null);
  const [filename, setFilename] = useState("");
  const [jd, setJd] = useState("");
  const [intent, setIntent] = useState<Intent>("polish");
  const [stream, setStream] = useState("");
  const [diffs, setDiffs] = useState<DiffItem[]>([]);
  const [adopted, setAdopted] = useState<Record<number, boolean>>({});
  const [polished, setPolished] = useState<ResumeStructured | null>(null);

  async function handleFile(file: File) {
    setError("");
    setState("UPLOADING");
    try {
      const { fileId, filename } = await uploadResume(file);
      setFilename(filename);
      setState("PARSING");
      const parsed = await parseResume(fileId);
      setResume(parsed);
      setState("NEED_TARGET");
    } catch (e) {
      setError(String((e as Error).message));
      setState("PARSE_FAILED");
    }
  }

  async function runPolish() {
    if (!resume) return;
    setError("");
    setStream("");
    setDiffs([]);
    setState("POLISHING");
    await polishStream(resume, jd, intent, {
      onChunk: (t) => setStream((s) => s + t),
      onDiff: (res) => {
        setDiffs(res.diffs);
        setPolished(res.resume);
        const init: Record<number, boolean> = {};
        res.diffs.forEach((_, i) => (init[i] = true));
        setAdopted(init);
      },
      onError: (msg) => {
        setError(msg);
        setState("POLISH_FAILED");
      },
      onDone: () => setState("REVIEW"),
    });
  }

  async function doExport() {
    if (!polished) return;
    setState("EXPORTING");
    try {
      await exportResume(polished);
      setState("DONE");
    } catch (e) {
      setError(String((e as Error).message));
      setState("REVIEW");
    }
  }

  const adoptedCount = Object.values(adopted).filter(Boolean).length;

  return (
    <>
      <header>
        <div className="logo" />
        <h1>AI 智能求职辅导 · 简历润色</h1>
        <span className="tag">前后端分离 · 首字响应 &lt;1s</span>
      </header>

      <div className="wrap">
        <div className="steps">
          {STEPS.map((s) => (
            <div
              key={s.label}
              className={"step" + (s.key.includes(state) ? " active" : "")}
            >
              {s.label}
            </div>
          ))}
        </div>

        {error && <div className="error">⚠ {error}</div>}

        <div className="grid">
          <div>
            <div className="card">
              <h2>① 上传简历</h2>
              <label
                className="drop"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files[0];
                  if (f) handleFile(f);
                }}
              >
                <input
                  type="file"
                  accept=".pdf,.docx"
                  hidden
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) handleFile(f);
                  }}
                />
                <p>
                  拖拽或 <b>点击上传</b>
                </p>
                <p className="hint">支持 PDF / DOCX，≤ 10MB</p>
              </label>
              {filename && (
                <div className="meta">
                  {state === "PARSING" ? "⏳ 解析中…" : "✅ 已解析"}：
                  <b>{filename}</b>
                </div>
              )}
            </div>

            <div className="card" style={{ marginTop: 14 }}>
              <h2>② 目标岗位（可选）</h2>
              <textarea
                value={jd}
                onChange={(e) => setJd(e.target.value)}
                placeholder="粘贴目标岗位 JD，AI 将对齐关键词与能力项…"
              />
              <div className="seg">
                {INTENTS.map((it) => (
                  <button
                    key={it.v}
                    className={intent === it.v ? "on" : ""}
                    onClick={() => setIntent(it.v)}
                  >
                    {it.label}
                  </button>
                ))}
              </div>
              <button
                className="btn"
                disabled={!resume || state === "POLISHING"}
                onClick={runPolish}
              >
                {state === "POLISHING" ? "AI 润色中…" : "开始 AI 润色"}
              </button>
              <div className="meta">大模型 API 仅在后端调用，前端不持有密钥。</div>
            </div>
          </div>

          <div>
            <div className="card">
              <h2>
                ③ 润色结果{" "}
                <span className="pill">
                  {state === "POLISHING"
                    ? "生成中"
                    : diffs.length || stream
                    ? "已完成"
                    : "待开始"}
                </span>
              </h2>
              <div className="stream">
                {stream || "上传简历并点击「开始 AI 润色」后，结果将在此处流式呈现…"}
                {state === "POLISHING" && <span className="cursor" />}
              </div>
            </div>

            <div className="card" style={{ marginTop: 14 }}>
              <h2>
                ④ 修改对比与采纳{" "}
                {diffs.length > 0 && (
                  <span className="hint">
                    已采纳 {adoptedCount}/{diffs.length} 处
                  </span>
                )}
              </h2>
              {diffs.length === 0 ? (
                <div className="hint">润色完成后展示逐处修改对比。</div>
              ) : (
                diffs.map((d, i) => (
                  <div key={i} className="diff-row">
                    <div className="diff-head">
                      <span className="pill">{d.section}</span> 第 {i + 1} 处
                    </div>
                    <div className="diff-cols">
                      <div className="col orig">{d.original}</div>
                      <div className="col new">{d.polished}</div>
                    </div>
                    <div className="reason">💡 {d.reason}</div>
                    <div className="acts">
                      <button
                        className={"ok" + (adopted[i] ? " sel" : "")}
                        onClick={() => setAdopted({ ...adopted, [i]: true })}
                      >
                        ✓ 采纳
                      </button>
                      <button
                        className={"no" + (!adopted[i] ? " sel" : "")}
                        onClick={() => setAdopted({ ...adopted, [i]: false })}
                      >
                        ↩ 保留原文
                      </button>
                    </div>
                  </div>
                ))
              )}
              <button
                className="btn"
                disabled={!polished}
                style={{ marginTop: 6 }}
                onClick={doExport}
              >
                ⑤ 导出润色后简历（PDF）
                {state === "DONE" && " · 已下载 ✅"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
