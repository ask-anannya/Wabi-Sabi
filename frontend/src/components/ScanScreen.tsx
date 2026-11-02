import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Camera, Loader2, MessageCircle, Pause, Play, RotateCcw, Upload } from "lucide-react";
import { postScan } from "../services/api";
import { speech } from "../services/speech";
import TrustLine from "./TrustLine";
import ProgressView from "./ProgressView";
import HonestMatchCard from "./HonestMatchCard";
import ReactionAlertCard from "./ReactionAlertCard";
import Button from "./ui/Button";
import type { ScanResponse } from "../entities/types";

// Turns a scan result into a natural-language message so the chat
// assistant can pick up the conversation with full context, the same way
// a user would describe their results out loud.
function buildScanSummary(result: ScanResponse): string {
  const metricLines = result.metrics
    .map((m) => `${m.name.replace("_", " ")}: ${m.band} (score ${Math.round(m.raw_score)}/100)`)
    .join(", ");
  const adviceLines = result.advice.map((a) => a.text).join(" ");
  const trustPct = Math.round(result.trust.score * 100);

  return (
    `I just did a skin scan with Wabi-Sabi. Here's what it found — ${metricLines}. ` +
    `Overall confidence: ${result.trust.band.replace("_", " ")} (${trustPct}%). ` +
    (adviceLines ? `The scan's advice was: ${adviceLines} ` : "") +
    `What's your take on these results, and what would you suggest I do next?`
  );
}

const MAX_LONG_SIDE = 4096;

// Client-side resize to the YouCam image spec (long side <=4096). Short-side
// minimum (1080) can't be fixed client-side without upscaling, which can't
// manufacture real resolution, so under-spec short sides are left to the
// server to reject/resize.
async function resizeToSpec(file: File): Promise<File> {
  const bitmap = await createImageBitmap(file);
  const longSide = Math.max(bitmap.width, bitmap.height);
  if (longSide <= MAX_LONG_SIDE) return file;

  const scale = MAX_LONG_SIDE / longSide;
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const ctx = canvas.getContext("2d");
  if (!ctx) return file;
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);

  const blob: Blob | null = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
  if (!blob) return file;
  return new File([blob], file.name, { type: "image/jpeg" });
}

type ScanStatus = "idle" | "uploading" | "analysing" | "ready" | "error";

interface ScanScreenProps {
  userId: string;
  onTalkToAssistant?: (summary: string) => void;
  onSeeMatches?: () => void;
}

const ScanScreen: React.FC<ScanScreenProps> = ({ userId, onTalkToAssistant, onSeeMatches }) => {
  const [resolvedAlerts, setResolvedAlerts] = useState<number[]>([]);
  const [status, setStatus] = useState<ScanStatus>("idle");
  const [result, setResult] = useState<ScanResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPreparingVoice, setIsPreparingVoice] = useState(false);
  const [uploadedPreviewUrl, setUploadedPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const spokenOnceRef = useRef(false);

  // Revoke the object URL whenever it's replaced or the screen unmounts, so
  // we don't leak blob URLs across repeated scans.
  useEffect(() => {
    return () => {
      if (uploadedPreviewUrl) URL.revokeObjectURL(uploadedPreviewUrl);
    };
  }, [uploadedPreviewUrl]);

  const statusMessage: Record<ScanStatus, string> = {
    idle: "",
    uploading: "Uploading your photo.",
    analysing: "Analysing your skin. This can take a few seconds.",
    ready: "Your results are ready.",
    error: `Something went wrong. ${errorMessage}`,
  };

  const handleFileSelected = async (file: File) => {
    setStatus("uploading");
    setErrorMessage("");
    spokenOnceRef.current = false;
    try {
      const resized = await resizeToSpec(file);
      setUploadedPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(resized);
      });
      setStatus("analysing");
      const scanResult = await postScan(resized, userId);
      setResult(scanResult);
      setStatus("ready");
      if (!spokenOnceRef.current) {
        spokenOnceRef.current = true;
        setIsPreparingVoice(true);
        speech.speak(
          scanResult.spoken_script,
          () => setIsPlaying(false),
          () => {
            setIsPreparingVoice(false);
            setIsPlaying(true);
          }
        );
      }
    } catch {
      setErrorMessage("Please check your connection and try again.");
      setStatus("error");
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelected(file);
    e.target.value = "";
  };

  const handleReplay = () => {
    if (!result) return;
    setIsPreparingVoice(true);
    speech.replay();
  };

  const handlePauseResume = () => {
    if (speech.isPaused()) {
      speech.resume();
      setIsPlaying(true);
    } else if (speech.isSpeaking()) {
      speech.pause();
      setIsPlaying(false);
    }
  };

  const handleRetake = () => {
    setResult(null);
    setStatus("idle");
    speech.stop();
    setIsPlaying(false);
    setIsPreparingVoice(false);
    setUploadedPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return null;
    });
  };

  const handleTalkToAssistant = () => {
    if (!result || !onTalkToAssistant) return;
    speech.stop();
    onTalkToAssistant(buildScanSummary(result));
  };

  const isBusy = status === "uploading" || status === "analysing";

  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-full overflow-y-auto p-6 bg-ink"
    >
      <div className="p-4 flex justify-center items-center border-b border-white/5 bg-ink-card shadow-soft mb-4 rounded-t-2xl">
        <div className="flex flex-col items-center">
          <p className="text-sm font-semibold text-gray-100">Skin Scan</p>
          <p className="text-xs text-gray-500">Voice-first — speak your results aloud</p>
        </div>
      </div>

      {/* Live region: announces upload/analyse/ready/error state changes for screen readers. */}
      <div role="status" aria-live="polite" className="sr-only">
        {statusMessage[status]}
      </div>
      <div role="status" aria-live="polite" className="sr-only">
        {isPreparingVoice ? "Preparing your voice." : ""}
      </div>

      {!result && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <label
            htmlFor="scan-file-input"
            className="flex flex-col items-center justify-center gap-2 w-64 h-64 rounded-3xl border-2 border-dashed border-white/15 bg-white/5 cursor-pointer hover:border-brand-500 transition focus-within:ring-2 focus-within:ring-brand-500"
          >
            {isBusy ? (
              <Loader2 size={40} className="animate-spin text-brand-400" aria-hidden="true" />
            ) : (
              <Camera size={40} className="text-gray-500" aria-hidden="true" />
            )}
            <span className="text-sm text-gray-400 text-center px-4">
              {isBusy ? statusMessage[status] : "Take or upload a photo to scan your skin"}
            </span>
            <input
              id="scan-file-input"
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="user"
              className="sr-only"
              onChange={handleInputChange}
              disabled={isBusy}
              aria-label="Upload a photo for skin scan"
            />
          </label>
          <span className="flex items-center gap-1 text-xs text-gray-400">
            <Upload size={14} aria-hidden="true" /> JPEG or PNG, well-lit, face centred
          </span>
          {status === "error" && (
            <p className="text-sm text-rose-400" role="alert">
              {statusMessage.error}
            </p>
          )}
        </div>
      )}

      {result && (
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-3 justify-center" role="group" aria-label="Playback controls">
              <Button
                onClick={handlePauseResume}
                aria-label={isPlaying ? "Pause narration" : "Resume narration"}
                variant="secondary"
                size="icon"
                disabled={isPreparingVoice}
              >
                {isPreparingVoice ? (
                  <Loader2 size={18} className="animate-spin" aria-hidden="true" />
                ) : isPlaying ? (
                  <Pause size={18} />
                ) : (
                  <Play size={18} />
                )}
              </Button>
              <Button
                onClick={handleReplay}
                aria-label="Replay narration"
                variant="secondary"
                size="icon"
                disabled={isPreparingVoice}
              >
                <RotateCcw size={18} />
              </Button>
            </div>
            {isPreparingVoice && <p className="text-xs text-gray-500">Preparing your voice…</p>}
          </div>

          <TrustLine band={result.trust.band} score={result.trust.score} spokenLine={result.trust.spoken_line} />

          {(result.overall_score !== null || result.skin_age !== null || result.inferred_skin_type) && (
            <dl className="grid grid-cols-3 gap-2 text-center" aria-label="YouCam skin summary">
              <div className="p-2 rounded-xl bg-ink-card border border-white/5">
                <dt className="text-[11px] text-gray-500">Skin score</dt>
                <dd className="text-lg font-semibold text-gray-100">{result.overall_score ?? "–"}</dd>
              </div>
              <div className="p-2 rounded-xl bg-ink-card border border-white/5">
                <dt className="text-[11px] text-gray-500">Skin age</dt>
                <dd className="text-lg font-semibold text-gray-100">{result.skin_age ?? "–"}</dd>
              </div>
              <div className="p-2 rounded-xl bg-ink-card border border-white/5">
                <dt className="text-[11px] text-gray-500">Skin type (detected)</dt>
                <dd className="text-lg font-semibold text-gray-100 capitalize">{result.inferred_skin_type ?? "–"}</dd>
              </div>
            </dl>
          )}

          {result.reading_summary && (
            <p className="text-sm text-gray-200 leading-relaxed px-1">{result.reading_summary}</p>
          )}

          {uploadedPreviewUrl && (
            <figure className="flex flex-col items-center">
              <img
                src={uploadedPreviewUrl}
                alt="The photo you submitted for this scan"
                className="max-h-64 rounded-2xl border border-white/10 shadow-soft object-cover"
              />
              <figcaption className="text-xs text-gray-500 mt-1">Your photo</figcaption>
            </figure>
          )}

          {result.metrics.some((m) => m.output_image) && (
            <section aria-label="Per-metric analysis images">
              <h3 className="text-xs uppercase tracking-wide text-gray-500 mb-2">Analysis</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {result.metrics
                  .filter((m) => m.output_image)
                  .map((m) => (
                    <figure key={m.name} className="flex flex-col items-center">
                      {/* YouCam masks are transparent overlays: layer each on the photo so the
                          highlighted areas land on the face they describe. */}
                      <div className="relative w-full aspect-[3/4] rounded-xl overflow-hidden border border-white/10 shadow-soft bg-ink-card">
                        {uploadedPreviewUrl && (
                          <img
                            src={uploadedPreviewUrl}
                            alt=""
                            aria-hidden="true"
                            className="absolute inset-0 w-full h-full object-contain opacity-70"
                          />
                        )}
                        <img
                          src={m.output_image as string}
                          alt={`YouCam's annotated ${m.name.replace("_", " ")} analysis, band: ${m.band}`}
                          className="absolute inset-0 w-full h-full object-contain"
                        />
                      </div>
                      <figcaption className="text-xs text-gray-500 mt-1 capitalize">
                        {m.name.replace("_", " ")} · {m.band} · {Math.round(m.raw_score)}/100
                      </figcaption>
                    </figure>
                  ))}
              </div>
            </section>
          )}

          <ul className="space-y-3">
            {result.advice.map((item) => (
              <li key={item.metric} className="p-3 rounded-xl bg-ink-card border border-white/5 shadow-soft">
                <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">{item.metric.replace("_", " ")}</p>
                <p className="text-sm text-gray-200">{item.text}</p>
              </li>
            ))}
          </ul>

          {result.progress && <ProgressView progress={result.progress} />}

          {result.reaction_alerts
            ?.filter((a) => !resolvedAlerts.includes(a.reaction_id))
            .map((a) => (
              <ReactionAlertCard
                key={a.reaction_id}
                alert={a}
                userId={userId}
                onResolved={() => setResolvedAlerts((prev) => [...prev, a.reaction_id])}
              />
            ))}

          {result.honest_matches?.length > 0 && (
            <section aria-label="Honest picks for this reading" className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-xs uppercase tracking-wide text-gray-500">Honest picks for this reading</h3>
              </div>
              {result.honest_matches.map((m) => (
                <HonestMatchCard key={m.product.id} match={m} />
              ))}
              {onSeeMatches && (
                <button onClick={onSeeMatches} className="text-sm text-brand-400 hover:underline">
                  See all honest picks & hype-check a product →
                </button>
              )}
            </section>
          )}

          <div className="mt-auto flex flex-col items-center gap-2">
            {onTalkToAssistant && (
              <Button onClick={handleTalkToAssistant} variant="dark" icon={MessageCircle}>
                Talk to Wabi, the skincare assistant!
              </Button>
            )}
            <Button onClick={handleRetake} variant="primary">
              Scan again
            </Button>
          </div>
        </div>
      )}
    </motion.div>
  );
};

export default ScanScreen;
