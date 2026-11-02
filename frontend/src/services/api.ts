import axios from "axios";
import type {
  AuthUser,
  Catalog,
  HonestMatch,
  MatchesResult,
  Message,
  ProfileView,
  ReactionAlert,
  RoutineContent,
  ScanHistoryEntry,
  ScanResponse,
  Severity,
  UsageEntry,
} from "../entities/types";
import { datadogRum } from "@datadog/browser-rum";

// VITE_API_BASE_URL lets a deployed frontend point at wherever the backend
// actually lives (set at build time) without another code change. Falls
// back to the old hostname-based guess if it's not set.
const envApiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;

if (envApiBaseUrl) {
  axios.defaults.baseURL = envApiBaseUrl;
} else if (window.location.hostname === "localhost") {
  axios.defaults.baseURL = "http://localhost:8000/api/v1";
} else {
  axios.defaults.baseURL = "https://api.wabi-sabi.beauty/api/v1";
}

const api = axios.create({
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

async function chatLLM(prompt: Message[]): Promise<string|RoutineContent> {
  try {
    var langPrompt = {
      messages: prompt,
    };
    const start = performance.now();
    const response = await api.post("/llm/chat", langPrompt);
    datadogRum.addTiming("llm_time_to_first_token", performance.now() - start);
    datadogRum.addAction("backend_api_called", {
      endpoint: "/llm/chat",
      method: "POST",
    });
    if (response.status !== 200) {
      console.error("Error communicating with LLM API:", response.data);
      return Promise.reject("Something went wrong with LLM API");
    } else {
      if (!response.data || !response.data.result) {
        return Promise.reject("No response from LLM API");
      }
      return response.data.result;
    }
  } catch (error) {
    datadogRum.addError(error, {
      source: "chat_api",
      endpoint: "/api/chat",
      userAction: "send_message",
    });
    console.error("Error communicating with LLM API:", error);
    throw error;
  }
}

interface ScanProfile {
  age?: number;
  skinType?: string;
  concerns?: string[];
}

async function postScan(
  imageFile: File,
  userId: string,
  profile?: ScanProfile
): Promise<ScanResponse> {
  const form = new FormData();
  form.append("image", imageFile);
  form.append("user_id", userId);
  if (profile?.age !== undefined) form.append("age", String(profile.age));
  if (profile?.skinType) form.append("skin_type", profile.skinType);
  if (profile?.concerns?.length) form.append("concerns", profile.concerns.join(","));

  const start = performance.now();
  try {
    const response = await api.post<ScanResponse>("/scan", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    datadogRum.addTiming("scan_time_to_result", performance.now() - start);
    datadogRum.addAction("backend_api_called", {
      endpoint: "/scan",
      method: "POST",
    });
    return response.data;
  } catch (error) {
    datadogRum.addError(error, {
      source: "scan_api",
      endpoint: "/scan",
      userAction: "submit_scan",
    });
    throw error;
  }
}

async function getScanHistory(userId: string, limit = 10): Promise<ScanHistoryEntry[]> {
  const response = await api.get("/scan/history", {
    params: { user_id: userId, limit },
  });
  return response.data.result;
}

async function deleteScanHistoryEntry(scanId: number, userId: string): Promise<void> {
  await api.delete(`/scan/history/${scanId}`, {
    params: { user_id: userId },
  });
}

async function signInWithGoogle(credential: string): Promise<AuthUser> {
  const response = await api.post("/auth/google", { credential });
  return response.data.result;
}

async function synthesizeSpeech(text: string): Promise<Blob> {
  // Measured live: a ~100-word scan narration takes ~25s to synthesize.
  // Generous margin above that so a real (slow) success isn't mistaken
  // for a failure and sent to the browser-voice fallback.
  const response = await api.post(
    "/tts",
    { text },
    { responseType: "blob", timeout: 45000 }
  );
  return response.data;
}

// ---- Honest Match: profile, tolerance, matches ----

interface ProfileInput {
  skin_type: string | null;
  concerns: string[];
  sensitizers: string[];
  style_prefs: string[];
}

async function getProfile(userId: string): Promise<ProfileView> {
  const response = await api.get("/profile", { params: { user_id: userId } });
  return response.data;
}

async function submitQuiz(
  userId: string,
  profile: ProfileInput,
  burnedProductIds: string[],
  workedProductIds: string[]
): Promise<ProfileView> {
  const response = await api.post("/profile/quiz", {
    user_id: userId,
    ...profile,
    burned_product_ids: burnedProductIds,
    worked_product_ids: workedProductIds,
  });
  return response.data;
}

async function getCatalog(): Promise<Catalog> {
  const response = await api.get("/catalog");
  return response.data;
}

async function getMatches(userId: string, limit = 6): Promise<MatchesResult> {
  const response = await api.get("/matches", { params: { user_id: userId, limit } });
  return response.data;
}

async function getHonestCheck(productId: string, userId: string): Promise<{ match: HonestMatch }> {
  const response = await api.get(`/products/${productId}/honest`, { params: { user_id: userId } });
  return response.data;
}

async function getUsage(userId: string): Promise<UsageEntry[]> {
  const response = await api.get("/usage", { params: { user_id: userId } });
  return response.data.result;
}

async function startUsage(userId: string, productId: string): Promise<void> {
  await api.post("/usage", { user_id: userId, product_id: productId });
}

async function stopUsage(userId: string, productId: string): Promise<void> {
  await api.delete(`/usage/${productId}`, { params: { user_id: userId } });
}

async function postCheckin(userId: string, productId: string, severity: Severity): Promise<ProfileView> {
  const response = await api.post("/checkin", { user_id: userId, product_id: productId, severity });
  return response.data;
}

async function getPendingReactions(userId: string): Promise<ReactionAlert[]> {
  const response = await api.get("/reactions/pending", { params: { user_id: userId } });
  return response.data.result;
}

async function resolveReaction(userId: string, reactionId: number, confirmed: boolean): Promise<ProfileView> {
  const response = await api.post(`/reactions/${reactionId}/resolve`, { user_id: userId, confirmed });
  return response.data;
}

export {
  getProfile,
  submitQuiz,
  getCatalog,
  getMatches,
  getHonestCheck,
  getUsage,
  startUsage,
  stopUsage,
  postCheckin,
  getPendingReactions,
  resolveReaction,
};
export { chatLLM, postScan, getScanHistory, deleteScanHistoryEntry, signInWithGoogle, synthesizeSpeech };
