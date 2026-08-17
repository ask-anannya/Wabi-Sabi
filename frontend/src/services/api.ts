import axios from "axios";
import type { AuthUser, Message, RoutineContent, ScanHistoryEntry, ScanResponse } from "../entities/types";
import { datadogRum } from "@datadog/browser-rum";

if (window.location.hostname === "localhost") {
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

export { chatLLM, postScan, getScanHistory, deleteScanHistoryEntry, signInWithGoogle, synthesizeSpeech };
