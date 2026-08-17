import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Send, Loader2 } from "lucide-react";
import ChatBubble from "./ChatBubble";
import TypingIndicator from "./TypingIndicator";
import Button from "./ui/Button";
import type { Message, Profile, RoutineStep } from "../entities/types";

const handleKeyPress = (
  e: React.KeyboardEvent<HTMLInputElement>,
  handler: () => void
): void => {
  if (e.key === "Enter") {
    handler();
  }
};

interface ChatbotScreenProps {
  messages: Message[];
  isTyping: boolean;
  input: string;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  sendMessage: (msg: string) => void;
  openModal: (step: RoutineStep, warnings: string[], profile: Profile) => void;
  chatRef: React.RefObject<HTMLDivElement | null>;
}

const ChatbotScreen: React.FC<ChatbotScreenProps> = ({
  messages,
  isTyping,
  input,
  setInput,
  sendMessage,
  openModal,
  chatRef,
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: 50 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
      className="flex flex-col h-full overflow-hidden bg-ink"
    >
      <div className="p-4 flex justify-center items-center border-b border-white/5 bg-ink-card/80 backdrop-blur-sm shadow-soft">
        <div className="flex flex-col items-center">
          <p className="text-sm font-semibold text-gray-100">Wabi-Sabi AI</p>
          <p className="text-xs text-gray-500">Online</p>
        </div>
      </div>

      <div
        ref={chatRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 bg-ink"
      >
        {messages.length === 0 && !isTyping && (
          <div className="h-full flex flex-col items-center justify-center text-center gap-3 text-gray-500 px-8">
            <MessageCircle size={32} aria-hidden="true" />
            <p className="text-sm">
              Ask me anything about your skin — routines, ingredients, or how you're feeling about a recent scan.
            </p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {messages.map((msg, index) => (
            <ChatBubble
              key={index}
              role={msg.role}
              content={msg.content}
              openModal={openModal}
            />
          ))}
        </AnimatePresence>

        {isTyping && (
          <div className="flex justify-start">
            <TypingIndicator />
          </div>
        )}
      </div>

      <div className="p-4 bg-ink-card flex items-center gap-3 border-t border-white/5 shadow-inner">
        <div className="flex items-center bg-white/10 p-3 rounded-full flex-1">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => handleKeyPress(e, () => sendMessage(input))}
            type="text"
            placeholder="Ask the AI"
            className="bg-transparent outline-none w-full text-sm text-gray-100 placeholder-gray-500"
          />
        </div>

        <Button
          onClick={() => sendMessage(input)}
          disabled={isTyping}
          aria-label="Send message"
          size="icon"
          variant={input.trim() ? "primary" : "secondary"}
          className={!input.trim() ? "text-gray-400 hover:-translate-y-0 hover:shadow-soft cursor-not-allowed" : ""}
        >
          {isTyping ? (
            <Loader2 size={24} className="animate-spin" aria-hidden="true" />
          ) : (
            <Send size={20} aria-hidden="true" />
          )}
        </Button>
      </div>
    </motion.div>
  );
};

export default ChatbotScreen;
