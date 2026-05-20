export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type LessonItem = {
  id: string;
  language: string;
  mode: string;
  topic: string;
  difficulty: string;
  text_fr: string;
  text_en: string;
  expected_keywords: string[];
};

export type LessonPack = {
  id: string;
  language: string;
  title: string;
  description: string;
  topics: string[];
  items: LessonItem[];
};

export type LessonCatalog = {
  packs: LessonPack[];
};

export type STTSegment = {
  start: number;
  end: number;
  text: string;
};

export type STTResponse = {
  audio_asset_id: string;
  transcript: string;
  language: string;
  duration_seconds: number | null;
  segments: STTSegment[];
};

export type PracticeScore = {
  score: number;
  label: string;
  feedback: string;
  missing_words: string[];
  extra_words: string[];
};

export type PracticeAttemptResponse = {
  attempt_id: string;
  session_id: string;
  practice_item_id: string;
  target_text: string;
  transcript: string;
  score: PracticeScore;
};

export type ConversationResponse = {
  turn_id: string;
  child_text: string;
  tutor_reply: string;
  topic: string | null;
};

export type QuestionResponse = {
  turn_id: string;
  question: string;
  tutor_reply: string;
};

export type DiscussionStartResponse = {
  session_id: string;
  topic: string;
  tutor_reply: string;
};

export type DiscussionAnswerResponse = {
  session_id: string;
  turn_id: string;
  topic: string;
  child_text: string;
  feedback: string;
  tutor_reply: string;
  needs_improvement: boolean;
  turn_index: number;
};

export type TTSResponse = {
  audio_asset_id: string;
  audio_url: string;
  content_type: string;
  text: string;
  language: string;
};

export type ChildDashboard = {
  family_id: string;
  child_id: string;
  stars: number;
  words_practiced: number;
  attempts_today: number;
  total_attempts: number;
  average_score: number | null;
  recent_wins: string[];
};

export type ParentDashboard = {
  family_id: string;
  child_id: string;
  total_attempts: number;
  average_score: number | null;
  weak_topics: Array<{
    topic: string;
    attempts: number;
    average_score: number;
  }>;
  recent_attempts: Array<{
    attempt_id: string;
    practice_item_id: string;
    topic: string | null;
    target_text: string;
    transcript: string;
    score: number;
    feedback: string;
    created_at: string;
  }>;
};

export type PracticeSettings = {
  id: string;
  family_id: string;
  child_id: string;
  difficulty: string;
  daily_goal_minutes: number;
  preferred_topics: string[];
};

export async function fetchLessons(): Promise<LessonCatalog> {
  const response = await fetch(`${API_BASE_URL}/lessons`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Lesson request failed with ${response.status}`);
  }

  return response.json();
}

export async function transcribeFrenchAudio(audio: Blob): Promise<STTResponse> {
  const formData = new FormData();
  formData.append("family_id", "local-family");
  formData.append("language", "fr");
  formData.append("file", audio, "practice.webm");

  const response = await fetch(`${API_BASE_URL}/stt/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Transcription failed with ${response.status}`);
  }

  return response.json();
}

export async function submitPracticeAttempt(params: {
  item: LessonItem;
  transcript: string;
  audioAssetId?: string;
}): Promise<PracticeAttemptResponse> {
  const response = await fetch(`${API_BASE_URL}/practice/attempt`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      practice_item_id: params.item.id,
      target_text: params.item.text_fr,
      transcript: params.transcript,
      mode: params.item.mode,
      audio_asset_id: params.audioAssetId,
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Practice attempt failed with ${response.status}`);
  }

  return response.json();
}

export async function sendConversationMessage(params: {
  childText: string;
  topic?: string;
  difficulty?: string;
}): Promise<ConversationResponse> {
  const response = await fetch(`${API_BASE_URL}/conversation/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      child_text: params.childText,
      topic: params.topic,
      difficulty: params.difficulty ?? "beginner",
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Conversation failed with ${response.status}`);
  }

  return response.json();
}

export async function askMyQuestion(params: {
  question: string;
  difficulty?: string;
}): Promise<QuestionResponse> {
  const response = await fetch(`${API_BASE_URL}/question/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      question: params.question,
      difficulty: params.difficulty ?? "beginner",
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Question failed with ${response.status}`);
  }

  return response.json();
}

export async function startDiscussion(params: {
  topic: string;
  difficulty?: string;
}): Promise<DiscussionStartResponse> {
  const response = await fetch(`${API_BASE_URL}/discussion/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      topic: params.topic,
      difficulty: params.difficulty ?? "beginner",
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Discussion start failed with ${response.status}`);
  }

  return response.json();
}

export async function answerDiscussion(params: {
  sessionId: string;
  childText: string;
}): Promise<DiscussionAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/discussion/answer`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      session_id: params.sessionId,
      child_text: params.childText,
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Discussion answer failed with ${response.status}`);
  }

  return response.json();
}

export async function fetchChildDashboard(): Promise<ChildDashboard> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/child/local-child?family_id=local-family`,
    { headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Child dashboard failed with ${response.status}`);
  }

  return response.json();
}

export async function fetchParentDashboard(): Promise<ParentDashboard> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard/parent/local-child?family_id=local-family`,
    { headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Parent dashboard failed with ${response.status}`);
  }

  return response.json();
}

export async function synthesizeFrenchSpeech(text: string): Promise<TTSResponse> {
  const response = await fetch(`${API_BASE_URL}/tts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      text,
      language: "fr",
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `TTS failed with ${response.status}`);
  }

  return response.json();
}

export function resolveApiUrl(pathOrUrl: string): string {
  if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
    return pathOrUrl;
  }

  return `${API_BASE_URL}${pathOrUrl}`;
}

export async function fetchPracticeSettings(): Promise<PracticeSettings> {
  const response = await fetch(
    `${API_BASE_URL}/settings/local-child?family_id=local-family`,
    { headers: { Accept: "application/json" } },
  );

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Settings request failed with ${response.status}`);
  }

  return response.json();
}

export async function updatePracticeSettings(params: {
  difficulty?: string;
  dailyGoalMinutes?: number;
  preferredTopics?: string[];
}): Promise<PracticeSettings> {
  const response = await fetch(`${API_BASE_URL}/settings`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      family_id: "local-family",
      child_id: "local-child",
      difficulty: params.difficulty,
      daily_goal_minutes: params.dailyGoalMinutes,
      preferred_topics: params.preferredTopics,
    }),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new Error(detail ?? `Settings update failed with ${response.status}`);
  }

  return response.json();
}

async function readErrorDetail(response: Response): Promise<string | null> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    return null;
  }

  return null;
}
