"use client";

import { Mic, Play, RotateCcw, Send, SkipForward, Square } from "lucide-react";
import type { FormEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  askMyQuestion,
  answerDiscussion,
  ChildDashboard,
  fetchChildDashboard,
  fetchLessons,
  fetchParentDashboard,
  fetchPracticeSettings,
  LessonItem,
  ParentDashboard,
  PracticeSettings,
  PracticeScore,
  resolveApiUrl,
  sendConversationMessage,
  startDiscussion,
  submitPracticeAttempt,
  synthesizeFrenchSpeech,
  transcribeFrenchAudio,
  updatePracticeSettings,
} from "@/lib/api";

const fallbackItems: LessonItem[] = [
  {
    id: "local-fallback-bonjour",
    language: "fr",
    mode: "listen_repeat",
    topic: "greetings",
    difficulty: "beginner",
    text_fr: "Bonjour.",
    text_en: "Hello.",
    expected_keywords: ["bonjour"],
  },
];

const modes = ["listen_repeat", "vocabulary", "conversation", "my_question", "discussion"] as const;
type RecordingState = "idle" | "recording" | "transcribing";
type ConversationTurn = {
  childText: string;
  tutorReply: string;
};
type QuestionTurn = {
  question: string;
  tutorReply: string;
};
type DiscussionTurn = {
  childText: string;
  feedback: string;
  tutorReply: string;
  needsImprovement: boolean;
};
type AudioState = "idle" | "loading" | "playing";

export default function Home() {
  const [items, setItems] = useState<LessonItem[]>(fallbackItems);
  const [activeMode, setActiveMode] = useState<(typeof modes)[number]>("listen_repeat");
  const [activeIndex, setActiveIndex] = useState(0);
  const [difficulty, setDifficulty] = useState("beginner");
  const [dailyGoalMinutes, setDailyGoalMinutes] = useState(10);
  const [preferredTopics, setPreferredTopics] = useState<string[]>([]);
  const [settings, setSettings] = useState<PracticeSettings | null>(null);
  const [settingsStatus, setSettingsStatus] = useState("");
  const [status, setStatus] = useState("Loading French lessons...");
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [transcript, setTranscript] = useState("");
  const [practiceScore, setPracticeScore] = useState<PracticeScore | null>(null);
  const [conversationTurns, setConversationTurns] = useState<ConversationTurn[]>([
    {
      childText: "",
      tutorReply: "Bonjour ! Comment ca va ?",
    },
  ]);
  const [questionText, setQuestionText] = useState("");
  const [questionTurns, setQuestionTurns] = useState<QuestionTurn[]>([]);
  const [questionStatus, setQuestionStatus] = useState("");
  const [discussionTopic, setDiscussionTopic] = useState("");
  const [discussionSessionId, setDiscussionSessionId] = useState("");
  const [discussionTurns, setDiscussionTurns] = useState<DiscussionTurn[]>([]);
  const [discussionStatus, setDiscussionStatus] = useState("");
  const [recordingError, setRecordingError] = useState("");
  const [savedAttempts, setSavedAttempts] = useState(0);
  const [stars, setStars] = useState(0);
  const [wordsPracticed, setWordsPracticed] = useState(0);
  const [childDashboard, setChildDashboard] = useState<ChildDashboard | null>(null);
  const [parentDashboard, setParentDashboard] = useState<ParentDashboard | null>(null);
  const [audioState, setAudioState] = useState<AudioState>("idle");
  const [audioError, setAudioError] = useState("");
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioCacheRef = useRef<Map<string, string>>(new Map());
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    fetchLessons()
      .then((catalog) => {
        const loadedItems = catalog.packs.flatMap((pack) => pack.items);
        if (loadedItems.length > 0) {
          setItems(loadedItems);
          setStatus(`${loadedItems.length} French practice items ready`);
        } else {
          setStatus("No French lessons found");
        }
      })
      .catch(() => {
        setStatus("Using local sample until the backend is running");
      });
  }, []);

  useEffect(() => {
    void refreshDashboards();
    void loadSettings();
  }, []);

  useEffect(() => {
    return () => {
      stopMicrophone();
      audioRef.current?.pause();
    };
  }, []);

  const visibleItems = useMemo(() => {
    const topicItems =
      preferredTopics.length > 0 &&
      activeMode !== "conversation" &&
      activeMode !== "my_question" &&
      activeMode !== "discussion"
        ? items.filter((item) => preferredTopics.includes(item.topic))
        : items;
    const modeItems = topicItems.filter((item) => item.mode === activeMode);
    return modeItems.length > 0 ? modeItems : items;
  }, [activeMode, items, preferredTopics]);

  const activeItem = visibleItems[activeIndex % visibleItems.length] ?? fallbackItems[0];
  const isConversationMode = activeMode === "conversation";
  const isQuestionMode = activeMode === "my_question";
  const isDiscussionMode = activeMode === "discussion";
  const displayedPrompt = isDiscussionMode
    ? discussionTurns[discussionTurns.length - 1]?.tutorReply || "Enter a topic to begin."
    : isQuestionMode
      ? questionTurns[questionTurns.length - 1]?.tutorReply || "Pose ta question."
      : isConversationMode
      ? conversationTurns[conversationTurns.length - 1]?.tutorReply ?? "Bonjour !"
      : activeItem.text_fr;
  const displayedTranslation = isDiscussionMode
    ? discussionTopic || "Discussion"
    : isQuestionMode
      ? "Type or record a question."
      : isConversationMode
      ? "Answer in simple French."
      : activeItem.text_en;
  const displayedTopic = isDiscussionMode
    ? "discussion"
    : isQuestionMode
      ? "my question"
    : isConversationMode
      ? "conversation"
      : activeItem.topic;

  async function loadSettings() {
    try {
      const loadedSettings = await fetchPracticeSettings();
      setSettings(loadedSettings);
      setDifficulty(loadedSettings.difficulty);
      setDailyGoalMinutes(loadedSettings.daily_goal_minutes);
      setPreferredTopics(loadedSettings.preferred_topics);
    } catch {
      setSettingsStatus("Settings will save when the backend is available.");
    }
  }

  async function saveSettings(nextSettings: {
    difficulty?: string;
    dailyGoalMinutes?: number;
    preferredTopics?: string[];
  }) {
    try {
      setSettingsStatus("Saving...");
      const saved = await updatePracticeSettings({
        difficulty,
        dailyGoalMinutes,
        preferredTopics,
        ...nextSettings,
      });
      setSettings(saved);
      setDifficulty(saved.difficulty);
      setDailyGoalMinutes(saved.daily_goal_minutes);
      setPreferredTopics(saved.preferred_topics);
      setSettingsStatus("Saved");
    } catch (error) {
      setSettingsStatus(error instanceof Error ? error.message : "Could not save settings.");
    }
  }

  function nextItem() {
    setActiveIndex((current) => current + 1);
    setTranscript("");
    setPracticeScore(null);
    setRecordingError("");
  }

  async function submitQuestion(question: string) {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion) {
      setQuestionStatus("Add a question first.");
      return;
    }

    try {
      setQuestionStatus("Asking tutor...");
      setRecordingError("");
      setAudioError("");
      const answer = await askMyQuestion({
        question: trimmedQuestion,
        difficulty,
      });
      setQuestionTurns((current) => [
        ...current,
        {
          question: trimmedQuestion,
          tutorReply: answer.tutor_reply,
        },
      ]);
      setQuestionText("");
      setSavedAttempts((current) => current + 1);
      setStatus("Tutor answered");
      setQuestionStatus("Answered");
      void playPromptAudio(answer.tutor_reply);
      void refreshDashboards();
    } catch (error) {
      setQuestionStatus(error instanceof Error ? error.message : "Could not answer question.");
    }
  }

  async function submitTypedQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuestion(questionText);
  }

  async function beginDiscussion() {
    const topic = discussionTopic.trim();
    if (!topic) {
      setDiscussionStatus("Add a topic first.");
      return;
    }

    try {
      setDiscussionStatus("Starting...");
      setTranscript("");
      setRecordingError("");
      const discussion = await startDiscussion({ topic, difficulty });
      setDiscussionSessionId(discussion.session_id);
      setDiscussionTurns([
        {
          childText: "",
          feedback: "",
          tutorReply: discussion.tutor_reply,
          needsImprovement: false,
        },
      ]);
      setDiscussionStatus("Started");
      void playPromptAudio(discussion.tutor_reply);
    } catch (error) {
      setDiscussionStatus(error instanceof Error ? error.message : "Could not start discussion.");
    }
  }

  async function playPromptAudio(text = displayedPrompt) {
    const spokenText = text.trim();
    if (!spokenText) {
      return;
    }

    try {
      setAudioError("");
      setAudioState("loading");
      let audioUrl = audioCacheRef.current.get(spokenText);
      if (!audioUrl) {
        const response = await synthesizeFrenchSpeech(spokenText);
        audioUrl = resolveApiUrl(response.audio_url);
        audioCacheRef.current.set(spokenText, audioUrl);
      }

      audioRef.current?.pause();
      const audio = new Audio(audioUrl);
      audioRef.current = audio;
      audio.onended = () => setAudioState("idle");
      audio.onerror = () => {
        setAudioState("idle");
        setAudioError("Could not play tutor audio.");
      };
      setAudioState("playing");
      await audio.play();
    } catch (error) {
      setAudioState("idle");
      setAudioError(error instanceof Error ? error.message : "Could not create tutor audio.");
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setRecordingError("This browser cannot record audio.");
      return;
    }
    if (isDiscussionMode && !discussionSessionId) {
      setRecordingError("Start a discussion first.");
      return;
    }

    try {
      setTranscript("");
      setPracticeScore(null);
      setRecordingError("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = chooseRecordingMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      chunksRef.current = [];
      streamRef.current = stream;
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        void submitRecording(recorder.mimeType || "audio/webm");
      };

      recorder.start();
      setRecordingState("recording");
      setStatus("Recording...");
    } catch (error) {
      setRecordingError(error instanceof Error ? error.message : "Could not start recording.");
      stopMicrophone();
      setRecordingState("idle");
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return;
    }

    setRecordingState("transcribing");
    setStatus("Transcribing French audio...");
    recorder.stop();
    stopMicrophone();
  }

  async function submitRecording(mimeType: string) {
    const audio = new Blob(chunksRef.current, { type: mimeType });
    chunksRef.current = [];

    if (audio.size === 0) {
      setRecordingError("No audio was recorded.");
      setRecordingState("idle");
      setStatus("Ready to try again");
      return;
    }

    try {
      const result = await transcribeFrenchAudio(audio);
      const heardText = result.transcript || "";
      setTranscript(heardText || "(No speech detected)");
      if (isConversationMode) {
        const turn = await sendConversationMessage({
          childText: heardText,
          topic: activeItem.topic,
          difficulty,
        });
        setConversationTurns((current) => [
          ...current,
          {
            childText: heardText,
            tutorReply: turn.tutor_reply,
          },
        ]);
        setSavedAttempts((current) => current + 1);
        setStatus("Tutor replied");
        void playPromptAudio(turn.tutor_reply);
      } else if (isQuestionMode) {
        await submitQuestion(heardText);
      } else if (isDiscussionMode) {
        const turn = await answerDiscussion({
          sessionId: discussionSessionId,
          childText: heardText,
        });
        setDiscussionTurns((current) => [
          ...current,
          {
            childText: heardText,
            feedback: turn.feedback,
            tutorReply: turn.tutor_reply,
            needsImprovement: turn.needs_improvement,
          },
        ]);
        setSavedAttempts((current) => current + 1);
        setStatus(turn.needs_improvement ? "Try that sentence once more" : "Next question ready");
        void playPromptAudio(turn.tutor_reply);
      } else {
        const attempt = await submitPracticeAttempt({
          item: activeItem,
          transcript: heardText,
          audioAssetId: result.audio_asset_id,
        });
        setPracticeScore(attempt.score);
        setSavedAttempts((current) => current + 1);
        setStars((current) => current + starsForScore(attempt.score.score));
        setWordsPracticed((current) => current + activeItem.expected_keywords.length);
        setStatus("Feedback ready");
      }
      void refreshDashboards();
    } catch (error) {
      setRecordingError(error instanceof Error ? error.message : "Transcription failed.");
      setStatus("Could not transcribe audio");
    } finally {
      setRecordingState("idle");
      mediaRecorderRef.current = null;
    }
  }

  function stopMicrophone() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }

  async function refreshDashboards() {
    try {
      const [child, parent] = await Promise.all([
        fetchChildDashboard(),
        fetchParentDashboard(),
      ]);
      setChildDashboard(child);
      setParentDashboard(parent);
      setStars(child.stars);
      setWordsPracticed(child.words_practiced);
      setSavedAttempts(parent.total_attempts);
    } catch {
      // Keep the local in-session counters if the backend dashboard is unavailable.
    }
  }

  return (
    <main className="min-h-screen bg-paper text-ink">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 px-5 py-5 sm:px-8 lg:px-10">
        <header className="flex flex-col gap-3 border-b border-ink/10 pb-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-normal text-meadow">
              AI Lingua
            </p>
            <h1 className="text-3xl font-bold sm:text-4xl">French Practice</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-sm font-semibold" htmlFor="difficulty">
              Difficulty
            </label>
            <select
              id="difficulty"
              value={difficulty}
              onChange={(event) => {
                const value = event.target.value;
                setDifficulty(value);
                void saveSettings({ difficulty: value });
              }}
              className="rounded-md border border-ink/20 bg-white px-3 py-2"
            >
              <option value="beginner">Beginner</option>
            </select>
          </div>
        </header>

        <section className="grid flex-1 gap-5 lg:grid-cols-[1.7fr_1fr]">
          <div className="flex flex-col gap-5 rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
            <nav className="grid grid-cols-2 gap-2 sm:grid-cols-5" aria-label="Practice modes">
              {modes.map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => {
                    setActiveMode(mode);
                    setActiveIndex(0);
                    setTranscript("");
                    setPracticeScore(null);
                    setRecordingError("");
                    setQuestionStatus("");
                  }}
                  className={`rounded-md px-3 py-3 text-sm font-bold capitalize ${
                    activeMode === mode
                      ? "bg-meadow text-white"
                      : "bg-ink/5 text-ink hover:bg-ink/10"
                  }`}
                >
                  {mode.replace("_", " ")}
                </button>
              ))}
            </nav>

            {isQuestionMode ? (
              <form
                onSubmit={(event) => void submitTypedQuestion(event)}
                className="grid gap-3 rounded-lg border border-ink/10 bg-ink/5 p-4 sm:grid-cols-[1fr_auto]"
              >
                <label className="block">
                  <span className="text-sm font-bold">My Question</span>
                  <input
                    value={questionText}
                    onChange={(event) => setQuestionText(event.target.value)}
                    className="mt-2 w-full rounded-md border border-ink/20 bg-white px-3 py-3"
                    placeholder="Comment dit-on apple ?"
                  />
                </label>
                <button
                  type="submit"
                  className="grid h-12 w-12 place-items-center self-end rounded-md bg-meadow text-white disabled:cursor-not-allowed disabled:bg-meadow/40"
                  aria-label="Ask question"
                  title="Ask question"
                  disabled={recordingState !== "idle" || !questionText.trim()}
                >
                  <Send size={22} />
                </button>
                {questionStatus ? (
                  <p className="text-sm font-semibold text-ink/70 sm:col-span-2">
                    {questionStatus}
                  </p>
                ) : null}
              </form>
            ) : null}

            {isDiscussionMode ? (
              <section className="grid gap-3 rounded-lg border border-ink/10 bg-ink/5 p-4 sm:grid-cols-[1fr_auto]">
                <label className="block">
                  <span className="text-sm font-bold">Topic</span>
                  <input
                    value={discussionTopic}
                    onChange={(event) => setDiscussionTopic(event.target.value)}
                    className="mt-2 w-full rounded-md border border-ink/20 bg-white px-3 py-3"
                    placeholder="food, football, school..."
                  />
                </label>
                <button
                  type="button"
                  onClick={() => void beginDiscussion()}
                  className="self-end rounded-md bg-meadow px-5 py-3 font-bold text-white disabled:cursor-not-allowed disabled:bg-meadow/40"
                  disabled={audioState === "loading"}
                >
                  Start
                </button>
                {discussionStatus ? (
                  <p className="text-sm font-semibold text-ink/70 sm:col-span-2">
                    {discussionStatus}
                  </p>
                ) : null}
              </section>
            ) : null}

            <div className="grid flex-1 place-items-center rounded-lg border border-dashed border-ink/20 bg-paper p-6 text-center">
              <div className="max-w-xl">
                <p className="mb-2 text-sm font-semibold uppercase tracking-normal text-berry">
                  {displayedTopic.replace("_", " ")}
                </p>
                <p className="text-5xl font-black leading-tight sm:text-6xl">
                  {displayedPrompt}
                </p>
                <p className="mt-4 text-xl text-ink/70">{displayedTranslation}</p>
              </div>
            </div>

            <div className="grid grid-cols-5 gap-3">
              <button
                type="button"
                onClick={() => void playPromptAudio()}
                className="grid h-16 place-items-center rounded-md bg-sky text-white disabled:cursor-not-allowed disabled:bg-sky/40"
                aria-label="Play prompt"
                title="Play prompt"
                disabled={audioState === "loading"}
              >
                <Play size={30} />
              </button>
              <button
                type="button"
                onClick={startRecording}
                className="col-span-2 grid h-16 place-items-center rounded-md bg-berry text-white disabled:cursor-not-allowed disabled:bg-berry/40"
                aria-label="Record"
                title="Record"
                disabled={recordingState !== "idle"}
              >
                <Mic size={34} />
              </button>
              <button
                type="button"
                onClick={stopRecording}
                className="grid h-16 place-items-center rounded-md bg-ink text-white disabled:cursor-not-allowed disabled:bg-ink/30"
                aria-label="Stop"
                title="Stop"
                disabled={recordingState !== "recording"}
              >
                <Square size={28} />
              </button>
              <button
                type="button"
                onClick={nextItem}
                className="grid h-16 place-items-center rounded-md bg-butter text-ink"
                aria-label="Next item"
                title="Next item"
              >
                <SkipForward size={30} />
              </button>
            </div>

            <div className="flex items-center justify-between gap-3 rounded-lg bg-meadow/10 px-4 py-3">
              <p className="text-sm font-semibold">
                {audioState === "loading" ? "Preparing tutor audio..." : status}
              </p>
              <button
                type="button"
                onClick={() => setActiveIndex(0)}
                className="grid h-10 w-10 place-items-center rounded-md bg-white text-meadow"
                aria-label="Restart list"
                title="Restart list"
              >
                <RotateCcw size={20} />
              </button>
            </div>

            <section className="rounded-lg border border-ink/10 bg-ink/5 p-4">
              <h2 className="text-lg font-bold">
                {isDiscussionMode
                  ? "Discussion"
                  : isQuestionMode
                    ? "My Question"
                  : isConversationMode
                    ? "Conversation"
                    : "What AI Lingua Heard"}
              </h2>
              <p className="mt-2 min-h-8 text-xl font-semibold">
                {transcript ||
                  (isQuestionMode
                    ? "Type a question above or record one with the microphone."
                    : "Record your French phrase to see the transcript here.")}
              </p>
              {isDiscussionMode ? (
                <div className="mt-4 max-h-72 space-y-3 overflow-auto rounded-md bg-white p-4">
                  {discussionTurns.length === 0 ? (
                    <p className="font-semibold text-ink/60">No discussion started.</p>
                  ) : null}
                  {discussionTurns.map((turn, index) => (
                    <div key={`${turn.tutorReply}-${index}`} className="space-y-1">
                      {turn.childText ? (
                        <p className="text-sm font-semibold text-ink/65">
                          You: {turn.childText}
                        </p>
                      ) : null}
                      {turn.feedback ? (
                        <p className="text-sm font-bold text-berry">
                          Feedback: {turn.feedback}
                        </p>
                      ) : null}
                      <p className="font-bold text-meadow">Tutor: {turn.tutorReply}</p>
                    </div>
                  ))}
                </div>
              ) : isQuestionMode ? (
                <div className="mt-4 max-h-56 space-y-3 overflow-auto rounded-md bg-white p-4">
                  {questionTurns.length === 0 ? (
                    <p className="font-semibold text-ink/60">No question asked yet.</p>
                  ) : null}
                  {questionTurns.map((turn, index) => (
                    <div key={`${turn.question}-${index}`} className="space-y-1">
                      <p className="text-sm font-semibold text-ink/65">
                        You: {turn.question}
                      </p>
                      <p className="font-bold text-meadow">Tutor: {turn.tutorReply}</p>
                    </div>
                  ))}
                </div>
              ) : isConversationMode ? (
                <div className="mt-4 max-h-56 space-y-3 overflow-auto rounded-md bg-white p-4">
                  {conversationTurns.map((turn, index) => (
                    <div key={`${turn.tutorReply}-${index}`} className="space-y-1">
                      {turn.childText ? (
                        <p className="text-sm font-semibold text-ink/65">
                          You: {turn.childText}
                        </p>
                      ) : null}
                      <p className="font-bold text-meadow">Tutor: {turn.tutorReply}</p>
                    </div>
                  ))}
                </div>
              ) : practiceScore ? (
                <div className="mt-4 grid gap-3 rounded-md bg-white p-4 sm:grid-cols-[120px_1fr]">
                  <div className="text-center">
                    <p className="text-4xl font-black text-meadow">{practiceScore.score}</p>
                    <p className="text-xs font-bold uppercase tracking-normal text-ink/60">
                      {practiceScore.label.replace("_", " ")}
                    </p>
                  </div>
                  <div>
                    <p className="font-bold">{practiceScore.feedback}</p>
                    {practiceScore.missing_words.length > 0 ? (
                      <p className="mt-2 text-sm text-ink/70">
                        Listen for: {practiceScore.missing_words.join(", ")}
                      </p>
                    ) : null}
                  </div>
                </div>
              ) : null}
              {recordingError ? (
                <p className="mt-3 rounded-md bg-berry/10 px-3 py-2 text-sm font-semibold text-berry">
                  {recordingError}
                </p>
              ) : null}
              {audioError ? (
                <p className="mt-3 rounded-md bg-berry/10 px-3 py-2 text-sm font-semibold text-berry">
                  {audioError}
                </p>
              ) : null}
            </section>
          </div>

          <aside className="flex flex-col gap-5">
            <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
              <h2 className="text-xl font-bold">Today</h2>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                <div className="rounded-md bg-butter/30 p-3">
                  <p className="text-2xl font-black">{stars}</p>
                  <p className="text-xs font-semibold">Stars</p>
                </div>
                <div className="rounded-md bg-sky/20 p-3">
                  <p className="text-2xl font-black">{wordsPracticed}</p>
                  <p className="text-xs font-semibold">Words</p>
                </div>
                <div className="rounded-md bg-meadow/15 p-3">
                  <p className="text-2xl font-black">
                    {childDashboard?.attempts_today ?? 0}
                  </p>
                  <p className="text-xs font-semibold">Today</p>
                </div>
              </div>
              {childDashboard?.average_score !== null && childDashboard?.average_score !== undefined ? (
                <p className="mt-4 rounded-md bg-ink/5 px-3 py-2 text-sm font-bold">
                  Average score: {childDashboard.average_score}
                </p>
              ) : null}
            </section>

            <section className="rounded-lg border border-ink/10 bg-white p-5 shadow-soft">
              <h2 className="text-xl font-bold">Parent View</h2>
              <div className="mt-4 space-y-3">
                <Metric label="Lesson items" value={String(items.length)} />
                <div className="rounded-md bg-ink/5 px-3 py-3">
                  <label className="text-sm font-semibold" htmlFor="daily-goal">
                    Daily goal
                  </label>
                  <div className="mt-2 flex items-center gap-2">
                    <input
                      id="daily-goal"
                      type="number"
                      min={1}
                      max={120}
                      value={dailyGoalMinutes}
                      onChange={(event) => setDailyGoalMinutes(Number(event.target.value))}
                      onBlur={() => void saveSettings({ dailyGoalMinutes })}
                      className="w-20 rounded-md border border-ink/20 bg-white px-2 py-1"
                    />
                    <span className="text-sm font-bold">min</span>
                  </div>
                </div>
                <div className="rounded-md bg-ink/5 px-3 py-3">
                  <p className="text-sm font-semibold">Topics</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {["greetings", "family", "food", "school"].map((topic) => {
                      const checked = preferredTopics.includes(topic);
                      return (
                        <label
                          key={topic}
                          className={`rounded-md px-2 py-1 text-xs font-bold ${
                            checked ? "bg-meadow text-white" : "bg-white text-ink"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => {
                              const nextTopics = checked
                                ? preferredTopics.filter((item) => item !== topic)
                                : [...preferredTopics, topic];
                              setPreferredTopics(nextTopics);
                              void saveSettings({ preferredTopics: nextTopics });
                            }}
                            className="sr-only"
                          />
                          {topic.replace("_", " ")}
                        </label>
                      );
                    })}
                  </div>
                </div>
                <Metric label="Saved attempts" value={String(savedAttempts)} />
                <Metric
                  label="Weak topic"
                  value={parentDashboard?.weak_topics[0]?.topic?.replace("_", " ") ?? "-"}
                />
              </div>
              {parentDashboard?.recent_attempts[0] ? (
                <div className="mt-4 rounded-md bg-ink/5 px-3 py-3">
                  <p className="text-xs font-bold uppercase tracking-normal text-ink/60">
                    Latest
                  </p>
                  <p className="mt-1 text-sm font-semibold">
                    {parentDashboard.recent_attempts[0].target_text} -{" "}
                    {parentDashboard.recent_attempts[0].score}
                  </p>
                </div>
              ) : null}
              {settingsStatus ? (
                <p className="mt-3 text-xs font-semibold text-ink/60">
                  {settingsStatus}
                </p>
              ) : null}
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}

function starsForScore(score: number) {
  if (score >= 90) {
    return 3;
  }
  if (score >= 70) {
    return 2;
  }
  if (score >= 45) {
    return 1;
  }
  return 0;
}

function chooseRecordingMimeType() {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  if (!("MediaRecorder" in window)) {
    return undefined;
  }

  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate));
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-md bg-ink/5 px-3 py-3">
      <span className="text-sm font-semibold">{label}</span>
      <span className="text-lg font-black">{value}</span>
    </div>
  );
}
