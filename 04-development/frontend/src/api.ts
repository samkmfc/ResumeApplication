import type { Intent, PolishResult, ResumeStructured } from "./types";

interface ExportRequestBody {
  resume: ResumeStructured;
  format: "pdf";
}

export async function uploadResume(
  file: File
): Promise<{ fileId: string; filename: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/resume/upload", { method: "POST", body: fd });
  if (!r.ok) throw new Error((await r.json()).detail ?? "上传失败");
  return r.json();
}

export async function parseResume(fileId: string): Promise<ResumeStructured> {
  const r = await fetch("/api/resume/parse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fileId }),
  });
  if (!r.ok) throw new Error((await r.json()).detail ?? "解析失败");
  return r.json();
}

interface PolishHandlers {
  onChunk: (text: string) => void;
  onDiff: (result: PolishResult) => void;
  onError: (msg: string) => void;
  onDone: () => void;
}

/** 发起润色并解析 SSE 事件流（meta / chunk / diff / error / done）。 */
export async function polishStream(
  resume: ResumeStructured,
  jd: string,
  intent: Intent,
  h: PolishHandlers
): Promise<void> {
  const r = await fetch("/api/polish", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume, jd, intent }),
  });
  if (!r.ok || !r.body) {
    h.onError("润色请求失败");
    return;
  }
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    // SSE 以空行分隔事件块
    const blocks = buf.split("\n\n");
    buf = blocks.pop() ?? "";
    for (const block of blocks) {
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      const parsed = JSON.parse(data);
      if (event === "chunk") h.onChunk(parsed.text ?? "");
      else if (event === "diff") h.onDiff(parsed as PolishResult);
      else if (event === "error") h.onError(parsed.message ?? "未知错误");
      else if (event === "done") h.onDone();
    }
  }
}

/** 导出 PDF 并触发浏览器下载。 */
export async function exportResume(resume: ResumeStructured): Promise<void> {
  const body: ExportRequestBody = { resume, format: "pdf" };
  const r = await fetch("/api/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error("导出失败");
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${resume.basics.name || "resume"}_润色版.pdf`;
  a.click();
  URL.revokeObjectURL(url);
}
