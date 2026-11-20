
'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Mic,
  Square,
  Volume2,
  PhoneOff,
  RotateCcw,
  Loader2,
} from 'lucide-react';

import Card from '../../../components/ui/Card';
import { api } from '../../../lib/api';

type State =
  | 'IDLE'
  | 'AI_SPEAKING'
  | 'LISTENING'
  | 'PROCESSING'
  | 'ANALYZING'
  | 'FOLLOW_UP_DECISION'
  | 'NEXT_QUESTION'
  | 'COMPLETING';

type SpeechRecognitionResultEvent = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      0: { transcript: string };
    };
  };
};

type SpeechRecognitionErrorEvent = {
  error: string;
};

type SpeechRecognitionInstance = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionInstance;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

export default function Interview() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [interview, setInterview] = useState<any>(null);
  const [q, setQ] = useState<any>(null);
  const [state, setState] = useState<State>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const [questionCount, setQuestionCount] = useState(1);
  const [elapsed, setElapsed] = useState(0);

  const recognition = useRef<SpeechRecognitionInstance | null>(null);
  const finalTranscript = useRef('');
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const mounted = useRef(true);
  const requestInProgress = useRef(false);

  // Start the interview and clean up when leaving the page.
  useEffect(() => {
    mounted.current = true;

    api
      .start(Number(id))
      .then((data) => {
        if (!mounted.current) return;

        setInterview(data.interview);
        setQ(data.question);
        setState('AI_SPEAKING');
      })
      .catch((e: Error) => {
        if (mounted.current) {
          setError(e.message || 'Could not start the interview.');
        }
      });

    return () => {
      mounted.current = false;
      window.speechSynthesis?.cancel();

      if (timer.current) {
        clearInterval(timer.current);
      }

      if (recognition.current) {
        const r = recognition.current;
        recognition.current = null;
        r.onend = null;
        r.onresult = null;
        r.onerror = null;

        try {
          r.stop();
        } catch {
          // Recognition may already have stopped.
        }
      }
    };
  }, [id]);

  // Read the interview question aloud.
  useEffect(() => {
    if (state !== 'AI_SPEAKING' || !q) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(q.question);
    utterance.rate = 0.94;

    utterance.onend = () => {
      if (mounted.current) setState('IDLE');
    };

    utterance.onerror = () => {
      if (mounted.current) setState('IDLE');
    };

    window.speechSynthesis.speak(utterance);

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [state, q]);

  // Update the elapsed interview timer.
 
const startTimeRef = useRef<number | null>(null);

useEffect(() => {
  if (!interview) return;

  const serverStart = interview.started_at
    ? new Date(interview.started_at).getTime()
    : NaN;

  startTimeRef.current = Number.isFinite(serverStart)
    ? serverStart
    : Date.now();

  const updateTimer = () => {
    if (startTimeRef.current === null) return;

    setElapsed(
      Math.max(0, Math.floor((Date.now() - startTimeRef.current) / 1000))
    );
  };

  updateTimer();
  timer.current = setInterval(updateTimer, 1000);

  return () => {
    if (timer.current) clearInterval(timer.current);
  };
}, [interview]);

  // Start microphone recording.
  function startMic() {
    setError('');

    if (state === 'ANALYZING' || state === 'COMPLETING') return;

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError(
        'Speech recognition is unavailable. Use Chrome or Edge, or type your answer below.'
      );
      return;
    }

    if (recognition.current) return;

    finalTranscript.current = '';
    setTranscript('');

    const r = new SpeechRecognition();
    recognition.current = r;

    r.continuous = true;
    r.interimResults = true;
    r.lang = 'en-IN';

    r.onresult = (event) => {
      let finalText = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const spokenText = result[0].transcript;

        if (result.isFinal) {
          finalText += spokenText + ' ';
        } else {
          interimText += spokenText;
        }
      }

      finalTranscript.current += finalText;

      if (mounted.current) {
        setTranscript(finalTranscript.current + interimText);
      }
    };

    r.onerror = (event) => {
      if (!mounted.current) return;

      setError(
        event.error === 'not-allowed'
          ? 'Microphone permission denied. Allow microphone access in your browser settings.'
          : `Speech recognition error: ${event.error}. You can type your answer instead.`
      );
    };

    r.onend = () => {
      if (recognition.current === r) {
        recognition.current = null;
      }

      if (mounted.current) {
        setTranscript(finalTranscript.current.trim());
        setState((current) =>
          current === 'LISTENING' ? 'IDLE' : current
        );
      }
    };

    try {
      r.start();
      setState('LISTENING');
    } catch {
      recognition.current = null;
      setState('IDLE');
      setError('Could not start the microphone. Please try again.');
    }
  }

  // Stop recording and keep the recognized answer.
  function stopMic() {
    const r = recognition.current;

    setState('IDLE');

    if (!r) {
      setTranscript(finalTranscript.current.trim());
      return;
    }

    r.onend = () => {
      if (recognition.current === r) {
        recognition.current = null;
      }

      if (mounted.current) {
        setTranscript(finalTranscript.current.trim());
        setState('IDLE');
      }
    };

    try {
      r.stop();
    } catch {
      recognition.current = null;
      setTranscript(finalTranscript.current.trim());
    }
  }

  // Submit the answer and request the next question.
  async function submit() {
    if (requestInProgress.current) return;

    setError('');

    if (recognition.current) {
      setError('Please stop recording and wait for the transcript before submitting.');
      return;
    }

    const text = transcript.trim();

    if (!text) {
      setError('No answer was captured. Speak or type your answer first.');
      return;
    }

    if (!q?.id) {
      setError('The current question is unavailable. Please try again.');
      return;
    }

    requestInProgress.current = true;
    setState('ANALYZING');

    try {
      await api.answer(Number(id), {
        question_id: q.id,
        transcript: text,
        audio_seconds: 0,
      });

      setState('NEXT_QUESTION');

      const nextQuestion = await api.next(Number(id));

      if (!mounted.current) return;

      if (!nextQuestion) {
        setError('No next question was returned by the server.');
        setState('IDLE');
        return;
      }

      setQ(nextQuestion);
      setQuestionCount(nextQuestion.question_number ?? questionCount + 1);
      setTranscript('');
      finalTranscript.current = '';
      setState('AI_SPEAKING');
    } catch (e: any) {
      if (mounted.current) {
        setError(e.message || 'Could not submit your answer.');
        setState('IDLE');
      }
    } finally {
      requestInProgress.current = false;
    }
  }

  // End the interview and navigate to the results.
  async function end() {
    if (requestInProgress.current) {
      setError('Please wait for the current answer to finish processing.');
      return;
    }

    requestInProgress.current = true;
    setState('COMPLETING');
    setError('');

    window.speechSynthesis.cancel();

    if (recognition.current) {
      const r = recognition.current;
      recognition.current = null;
      r.onend = null;
      r.onresult = null;
      r.onerror = null;

      try {
        r.stop();
      } catch {
        // Recognition may already have stopped.
      }
    }

    try {
      await api.complete(Number(id));

      if (mounted.current) {
        router.push(`/results/${id}`);
      }
    } catch (e: any) {
      if (mounted.current) {
        setError(e.message || 'Could not end the interview.');
        setState('IDLE');
      }
    } finally {
      requestInProgress.current = false;
    }
  }

  function repeat() {
    if (state === 'ANALYZING' || state === 'COMPLETING') return;

    setError('');
    setState('AI_SPEAKING');
  }

  const minutes = Math.floor(elapsed / 60)
    .toString()
    .padStart(2, '0');

  const seconds = (elapsed % 60).toString().padStart(2, '0');

  if (!q) {
    return (
      <main className="container py-10">
        {error || 'Initializing interview...'}
      </main>
    );
  }

  const statusText =
    state === 'AI_SPEAKING'
      ? 'Interviewer speaking...'
      : state === 'LISTENING'
        ? 'Recording your answer...'
        : state === 'ANALYZING'
          ? 'Analyzing your answer...'
          : state === 'COMPLETING'
            ? 'Ending interview...'
            : 'Ready for your answer';

  return (
    <main className="container max-w-6xl py-8">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <div className="badge">LIVE INTERVIEW</div>
          <h1 className="mt-3 text-xl font-bold">{interview?.role}</h1>
        </div>

        <button
          className="btn btn-danger gap-2"
          onClick={end}
          disabled={state === 'COMPLETING'}
        >
          <PhoneOff size={16} />
          End Interview
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-xl border border-red-900 bg-red-950/30 p-3 text-sm text-red-200"
        >
          {error}
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
        <Card className="flex min-h-[620px] flex-col p-8">
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <div
              className={`flex h-28 w-28 items-center justify-center rounded-full border border-[#333b49] bg-[#151a23] ${
                state === 'AI_SPEAKING' ? 'pulse' : ''
              }`}
            >
              <Volume2 size={36} />
            </div>

            <p className="muted mt-5 text-sm">{statusText}</p>

            <div className="mt-10 max-w-2xl">
              <div className="badge mb-4">
                {q.category} · {q.topic || 'Interview'}
              </div>

              <h2 className="text-2xl font-semibold leading-tight md:text-3xl">
                {q.question}
              </h2>
            </div>
          </div>

          <div>
            <textarea
              className="input min-h-28 resize-y"
              placeholder="Your spoken transcript will appear here. You can edit it or type your answer."
              value={transcript}
              onChange={(event) => setTranscript(event.target.value)}
              disabled={state === 'ANALYZING' || state === 'COMPLETING'}
            />

            <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
              <button
                className={`btn gap-2 ${
                  state === 'LISTENING' ? 'btn-primary' : 'btn-ghost'
                }`}
                onClick={state === 'LISTENING' ? stopMic : startMic}
                disabled={state === 'ANALYZING' || state === 'COMPLETING'}
              >
                {state === 'LISTENING' ? (
                  <>
                    <Square size={16} />
                    Stop Recording
                  </>
                ) : (
                  <>
                    <Mic size={16} />
                    Start Microphone
                  </>
                )}
              </button>

              <button
                className="btn btn-ghost gap-2"
                onClick={repeat}
                disabled={state === 'ANALYZING' || state === 'COMPLETING'}
              >
                <RotateCcw size={16} />
                Repeat
              </button>

              <button
                className="btn btn-primary"
                onClick={submit}
                disabled={state === 'ANALYZING' || state === 'COMPLETING'}
              >
                {state === 'ANALYZING' && (
                  <Loader2 className="mr-2 inline animate-spin" size={16} />
                )}
                Submit Answer
              </button>
            </div>
          </div>
        </Card>

        <aside className="space-y-4">
          <Card className="p-5">
            <p className="muted text-sm">Progress</p>

            <div className="mt-2 text-3xl font-bold">Q{questionCount}</div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#202733]">
              <div
                className="h-full bg-slate-300"
                style={{
                  width: `${Math.min(100, questionCount * 10)}%`,
                }}
              />
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4">
              <div>
                <p className="muted text-xs">Elapsed</p>
                <b>
                  {minutes}:{seconds}
                </b>
              </div>

              <div>
                <p className="muted text-xs">Mode</p>
                <b>{interview?.difficulty || 'Standard'}</b>
              </div>
            </div>
          </Card>

          <Card className="p-5">
            <p className="muted text-sm">Interview rules</p>

            <ul className="mt-3 text-sm leading-7 text-slate-300">
              <li>• One question at a time</li>
              <li>• Follow-ups adapt to your answer</li>
              <li>• No scores shown during interview</li>
              <li>• Repeat questions when needed</li>
            </ul>
          </Card>

          <Card className="p-5">
            <p className="muted text-xs uppercase tracking-wider">
              Voice State
            </p>

            <p className="mt-2 text-sm">
              {state === 'LISTENING' ? (
                <>
                  <Mic size={14} className="mr-2 inline" />
                  Microphone recording
                </>
              ) : (
                state.replaceAll('_', ' ')
              )}
            </p>
          </Card>
        </aside>
      </div>
    </main>
  );
}
