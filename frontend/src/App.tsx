import { useState, useRef, useEffect } from "react";
import { AnimatePresence } from "framer-motion";
import type { AuthUser, Message, Profile, RoutineStep, Screen } from "./entities/types";
import ChatbotScreen from "./components/ChatbotScreen";
import HistoryScreen from "./components/HistoryScreen";
import LandingScreen from "./components/LandingScreen";
import MatchesScreen from "./components/MatchesScreen";
import NavBar from "./components/NavBar";
import RoutineDetailModal from "./components/RoutineDetailModal";
import ScanScreen from "./components/ScanScreen";
import ToleranceScreen from "./components/ToleranceScreen";
import { chatLLM } from "./services/api";
import { datadogRum } from "@datadog/browser-rum";

const ANON_USER_ID_KEY = "wabi-sabi-user-id";
const AUTH_USER_KEY = "wabi-sabi-auth-user";

function getOrCreateAnonUserId(): string {
  let userId = localStorage.getItem(ANON_USER_ID_KEY);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(ANON_USER_ID_KEY, userId);
  }
  return userId;
}

function loadStoredAuthUser(): AuthUser | null {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

const App: React.FC = () => {
  const [screen, setScreen] = useState<Screen>("landing");
  const anonUserId = useRef<string>(getOrCreateAnonUserId());
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => loadStoredAuthUser());
  const userId = authUser?.user_id ?? anonUserId.current;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isTyping, setIsTyping] = useState<boolean>(false);

  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [selectedStepDetail, setSelectedStepDetail] =
    useState<RoutineStep | null>(null);
  const [currentWarnings, setCurrentWarnings] = useState<string[]>([]);
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null);

  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  const openModal = (
    stepData: RoutineStep,
    warnings: string[],
    profile: Profile
  ) => {
    setSelectedStepDetail(stepData);
    setCurrentWarnings(warnings);
    setCurrentProfile(profile);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedStepDetail(null);
    setCurrentWarnings([]);
    setCurrentProfile(null);
  };

  const sendMessage = (msg: string) => {
    datadogRum.addAction("chat_message_sent", {
      messageLength: msg.length,
      containsRoutineRequest: msg.toLowerCase().includes("routine"),
      timestamp: Date.now(),
    });
    if (!msg.trim()) return;

    const userMsg: Message = {
      role: "human",
      content: msg,
    };
    const newMessages: Message[] = [...messages, userMsg];
    setInput("");
    setMessages(newMessages);
    setScreen("chat");
    setIsTyping(true);

    chatLLM(newMessages)
      .then((response) => {
        setMessages((prev) => [...prev, { role: "ai", content: response }]);
        if (typeof response === "string") {
          datadogRum.addAction("chat_response_received", {
            responseLength: response.length,
            responseType: "general_advice",
          });
        }
      })
      .catch((error) => {
        console.error("LLM chat error:", error);
        datadogRum.addError("Error communicating with LLM API", {
          source: "chat_api",
          endpoint: "/api/chat",
          userAction: "send_message",
        });
        setMessages((prev) => [
          ...prev,
          {
            role: "ai",
            content: "Sorry, something went wrong. Please try again later.",
          },
        ]);
      })
      .finally(() => {
        setIsTyping(false);
      });
  };

  const handleTalkToAssistant = (summary: string) => {
    sendMessage(summary);
  };

  const handleStartScan = () => setScreen("scan");

  // Opens an empty chat ready for input — unlike sendMessage, this must not
  // require or push a message, since the user hasn't typed anything yet.
  const handleAskWabi = () => setScreen("chat");

  const handleSignIn = (user: AuthUser) => {
    setAuthUser(user);
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  };

  const handleSignOut = () => {
    setAuthUser(null);
    localStorage.removeItem(AUTH_USER_KEY);
  };

  return (
    <div className="h-screen w-screen bg-ink font-sans overflow-hidden flex flex-col">
      <NavBar
        screen={screen}
        onNavigate={setScreen}
        authUser={authUser}
        onSignIn={handleSignIn}
        onSignOut={handleSignOut}
      />

      <div className="relative flex-1 min-h-0">
        <AnimatePresence mode="wait">
          {screen === "scan" ? (
            <ScanScreen
              key="scan"
              userId={userId}
              onTalkToAssistant={handleTalkToAssistant}
              onSeeMatches={() => setScreen("matches")}
            />
          ) : screen === "matches" ? (
            <MatchesScreen key="matches" userId={userId} />
          ) : screen === "tolerance" ? (
            <ToleranceScreen key="tolerance" userId={userId} />
          ) : screen === "chat" ? (
            <ChatbotScreen
              key="chat"
              messages={messages}
              isTyping={isTyping}
              input={input}
              setInput={setInput}
              sendMessage={sendMessage}
              openModal={openModal}
              chatRef={chatRef}
            />
          ) : screen === "history" ? (
            <HistoryScreen key="history" userId={userId} />
          ) : (
            <LandingScreen key="landing" onStartScan={handleStartScan} onAskWabi={handleAskWabi} />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isModalOpen && (
            <RoutineDetailModal
              step={selectedStepDetail}
              warnings={currentWarnings}
              profile={currentProfile}
              onClose={closeModal}
            />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default App;
