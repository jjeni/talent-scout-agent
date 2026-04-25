const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface MatchBreakdown {
  skills_score: number;
  experience_score: number;
  location_score: number;
  education_score: number;
  total: number;
  top_reasons: string[];
  strengths: string[];
  gaps: string[];
}

export interface JDParseResult {
  role_title: string;
  seniority?: string;
  employment_type?: string;
  location?: {
    type: string;
    city?: string;
    constraint?: string;
  };
  experience?: { min_years?: number; preferred_years?: number };
  required_skills: { skill: string; importance: number }[];
  nice_to_have_skills: string[];
  compensation?: { min?: number; max?: number; currency: string; equity: boolean };
  urgency?: string;
  strengths?: string[];
  gaps?: string[];
}

export interface RankedCandidate {
  rank: number;
  candidate_id: string;
  candidate_name: string;
  match_score: number;
  interest_score: number;
  combined_score: number;
  top_match_reasons: string[];
  interest_summary: string;
  recruiter_note: string;
  source_type: string;
  data_completeness: number;
  strengths?: string[];
  gaps?: string[];
  key_signals?: string[];
  red_flags?: string[];
}

export interface ShortlistOutput {
  job_id: string;
  role_title: string;
  total_evaluated: number;
  shortlisted_count: number;
  avg_match_score: number;
  avg_interest_score: number;
  avg_combined_score: number;
  processing_time_seconds: number;
  ranked_candidates: RankedCandidate[];
  excluded_candidates: { candidate: string; reasons: string[] }[];
  weights: { match: number; interest: number };
}

export interface PipelineStatus {
  job_id: string;
  stage: string;
  progress: number;
  current_candidate?: string;
  message: string;
  error?: string;
}

export interface ConversationTurn {
  turn: number;
  agent: string;
  candidate: string;
}

export interface TranscriptData {
  candidate_id: string;
  turns: ConversationTurn[];
  total_turns: number;
  exit_reason?: string;
}

// ─── API Functions ────────────────────────────────────────────────────────────

const getHeaders = (base: any = {}) => {
  const headers = { ...base };
  if (typeof window !== "undefined") {
    const key = localStorage.getItem("TALENT_SCOUT_API_KEY");
    if (key) headers["X-Gemini-API-Key"] = key;
  }
  return headers;
};

export async function parseJD(jdText: string): Promise<JDParseResult> {
  const res = await fetch(`${BACKEND_URL}/api/parse-jd`, {
    method: "POST",
    headers: getHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jd_text: jdText }),
  });
  if (!res.ok) throw new Error(`JD parse failed: ${res.statusText}`);
  return res.json();
}

export async function startPipeline(params: {
  jobId: string;
  jdText: string;
  candidateUrls?: string[];
  useDefaultDataset?: boolean;
  topN?: number;
  wMatch?: number;
  wInterest?: number;
}): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${BACKEND_URL}/api/start-pipeline`, {
    method: "POST",
    headers: getHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      job_id: params.jobId,
      jd_text: params.jdText,
      candidate_urls: params.candidateUrls || [],
      use_default_dataset: params.useDefaultDataset ?? true,
      top_n: params.topN ?? 10,
      w_match: params.wMatch ?? 0.6,
      w_interest: params.wInterest ?? 0.4,
    }),
  });
  if (!res.ok) throw new Error(`Pipeline start failed: ${res.statusText}`);
  return res.json();
}

export async function startPipelineWithFiles(params: {
  jobId: string;
  jdText: string;
  files: File[];
  candidateUrls?: string[];
  useDefaultDataset?: boolean;
  topN?: number;
  wMatch?: number;
  wInterest?: number;
}): Promise<{ job_id: string; status: string; files_ingested: number }> {
  const form = new FormData();
  form.append("jd_text", params.jdText);
  form.append("job_id", params.jobId);
  form.append("use_default_dataset", String(params.useDefaultDataset ?? true));
  form.append("top_n", String(params.topN ?? 10));
  form.append("w_match", String(params.wMatch ?? 0.6));
  form.append("w_interest", String(params.wInterest ?? 0.4));
  form.append("candidate_urls", (params.candidateUrls || []).join("\n"));
  params.files.forEach((f) => form.append("files", f));

  const res = await fetch(`${BACKEND_URL}/api/start-pipeline-with-files`, {
    method: "POST",
    headers: getHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error(`Pipeline start failed: ${res.statusText}`);
  return res.json();
}

export async function getShortlist(jobId: string): Promise<ShortlistOutput> {
  const res = await fetch(`${BACKEND_URL}/api/shortlist/${jobId}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error(`Shortlist fetch failed: ${res.statusText}`);
  return res.json();
}

export async function getTranscript(jobId: string, candidateId: string): Promise<TranscriptData> {
  const res = await fetch(`${BACKEND_URL}/api/transcript/${jobId}/${candidateId}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error(`Transcript fetch failed: ${res.statusText}`);
  return res.json();
}

export async function getScoredCandidates(jobId: string) {
  const res = await fetch(`${BACKEND_URL}/api/scored-candidates/${jobId}`, {
    headers: getHeaders()
  });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

export function subscribePipelineStatus(
  jobId: string,
  onUpdate: (status: PipelineStatus) => void,
  onDone: () => void,
  onError: (err: string) => void
): () => void {
  let url = `${BACKEND_URL}/api/pipeline/status/${jobId}`;
  if (typeof window !== "undefined") {
    const key = localStorage.getItem("TALENT_SCOUT_API_KEY");
    if (key) url += `?api_key=${encodeURIComponent(key)}`;
  }
  const es = new EventSource(url);

  es.onmessage = (event) => {
    try {
      const data: PipelineStatus = JSON.parse(event.data);
      onUpdate(data);
      if (data.stage === "done" || data.stage === "error") {
        es.close();
        if (data.stage === "done") onDone();
        else onError(data.error || "Unknown error");
      }
    } catch {}
  };

  es.onerror = () => {
    es.close();
    onError("Connection to pipeline lost");
  };

  return () => es.close();
}
