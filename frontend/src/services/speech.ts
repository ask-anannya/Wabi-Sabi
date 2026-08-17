/**
 * Voice output. Tries the backend's Gemini-TTS endpoint first (a real,
 * warm-toned voice via /tts) and falls back to the browser's built-in
 * SpeechSynthesis if that request fails for any reason — narration must
 * never be a hard dependency on the network. Same public interface either
 * way, so callers (ScanScreen) don't need to know which mode is active.
 *
 * Gemini TTS synthesis is slow — measured ~25s for a ~100-word scan
 * narration — so `onStart` fires separately from the `speak()` call itself,
 * letting callers show a "preparing voice" state during that gap instead
 * of the UI looking hung.
 */

import { synthesizeSpeech } from "./api";

export interface SpeechController {
  supported: boolean;
  speak: (text: string, onEnd?: () => void, onStart?: () => void) => void;
  pause: () => void;
  resume: () => void;
  replay: () => void;
  stop: () => void;
  isSpeaking: () => boolean;
  isPaused: () => boolean;
}

function createSpeechController(): SpeechController {
  const browserSupported = typeof window !== "undefined" && "speechSynthesis" in window;
  let lastText = "";
  let lastOnEnd: (() => void) | undefined;
  let lastOnStart: (() => void) | undefined;
  let mode: "audio" | "browser" | "idle" = "idle";
  let audioEl: HTMLAudioElement | null = null;
  let currentObjectUrl: string | null = null;

  const revokeCurrentUrl = () => {
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = null;
    }
  };

  const speakWithBrowser = (text: string, onEnd?: () => void, onStart?: () => void) => {
    if (!browserSupported) return;
    mode = "browser";
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    if (onEnd) utterance.onend = onEnd;
    if (onStart) utterance.onstart = onStart;
    window.speechSynthesis.speak(utterance);
  };

  const speak = (text: string, onEnd?: () => void, onStart?: () => void) => {
    if (!text) return;
    lastText = text;
    lastOnEnd = onEnd;
    lastOnStart = onStart;

    // Stop whatever's currently playing before starting the new one.
    if (audioEl) audioEl.pause();
    if (browserSupported) window.speechSynthesis.cancel();

    synthesizeSpeech(text)
      .then((blob) => {
        revokeCurrentUrl();
        currentObjectUrl = URL.createObjectURL(blob);
        mode = "audio";
        audioEl = new Audio(currentObjectUrl);
        audioEl.onended = () => onEnd?.();
        audioEl.onerror = () => speakWithBrowser(text, onEnd, onStart);
        audioEl
          .play()
          .then(() => onStart?.())
          .catch(() => speakWithBrowser(text, onEnd, onStart));
      })
      .catch(() => speakWithBrowser(text, onEnd, onStart));
  };

  const pause = () => {
    if (mode === "audio") audioEl?.pause();
    else if (mode === "browser" && browserSupported) window.speechSynthesis.pause();
  };

  const resume = () => {
    if (mode === "audio") audioEl?.play().catch(() => {});
    else if (mode === "browser" && browserSupported) window.speechSynthesis.resume();
  };

  const replay = () => {
    if (lastText) speak(lastText, lastOnEnd, lastOnStart);
  };

  const stop = () => {
    audioEl?.pause();
    revokeCurrentUrl();
    if (browserSupported) window.speechSynthesis.cancel();
    mode = "idle";
  };

  const isSpeaking = () => {
    if (mode === "audio") return !!audioEl && !audioEl.paused && !audioEl.ended;
    if (mode === "browser") return browserSupported && window.speechSynthesis.speaking;
    return false;
  };

  const isPaused = () => {
    if (mode === "audio") return !!audioEl && audioEl.paused && !audioEl.ended;
    if (mode === "browser") return browserSupported && window.speechSynthesis.paused;
    return false;
  };

  return { supported: true, speak, pause, resume, replay, stop, isSpeaking, isPaused };
}

export const speech = createSpeechController();
