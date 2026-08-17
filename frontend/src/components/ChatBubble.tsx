import { motion } from "framer-motion";
import RoutineDisplay from "./RoutineDisplay";
import type { Message, Profile, RoutineStep } from "../entities/types";

interface ChatBubbleProps extends Message {
  openModal: (step: RoutineStep, warnings: string[], profile: Profile) => void;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({
  role,
  content,
  openModal,
}) => {
  const isUser = role === "human";

  const contentStr = content?.toString() || "";
  const textPart = contentStr.split("```json")[0].trim();
  let normalizedRoutine: any = null;

  if (typeof content === "object" && content?.type === "routine") {
    normalizedRoutine = {
      profile: content.data.profile,
      warnings: content.data.warnings || [],
      morning_routine: content.data.morning_routine || [],
      evening_routine: content.data.evening_routine || [],
      night_routine: content.data.night_routine || [],
    };
  }

  const alignment = isUser ? "justify-end" : "justify-start";
  const bubbleClasses = isUser
    ? "bg-brand-600 text-white rounded-t-xl rounded-bl-xl"
    : "bg-ink-card text-gray-100 rounded-t-xl rounded-br-xl shadow-soft";

  const avatar = isUser ? (
    <div className="w-8 h-8 rounded-full bg-orange-300 flex items-center justify-center text-sm font-semibold">
      U
    </div>
  ) : (
    <div className="w-8 h-8 rounded-full bg-rose-300 flex items-center justify-center text-sm font-semibold">
      S
    </div>
  );

  return (
    <>
      {(textPart && !normalizedRoutine) && (
        <motion.div
          layout
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
          className={`flex ${alignment} w-full`}
        >
          {!isUser && avatar}

          <div className={`p-3 text-sm mx-2 ${bubbleClasses} max-w-[85%]`}>
            {textPart}
          </div>

          {isUser && avatar}
        </motion.div>
      )}

      {normalizedRoutine && (
        <RoutineDisplay routine={normalizedRoutine} openModal={openModal} />
      )}
    </>
  );
};

export default ChatBubble;
