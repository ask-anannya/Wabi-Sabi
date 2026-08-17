import { Sun, Moon, ArrowRight, AlertTriangle } from "lucide-react";
import RoutineStepCard from "./RoutineStepCard";
import type { RoutineData, RoutineStep, Profile } from "../entities/types";

interface RoutineDisplayProps {
  routine: RoutineData;
  openModal: (step: RoutineStep, warnings: string[], profile: Profile) => void;
}

const RoutineDisplay: React.FC<RoutineDisplayProps> = ({
  routine,
  openModal,
}) => {
  if (!routine || !routine.profile) return null;

  interface RoutineSectionProps {
    title: string;
    steps: RoutineStep[];
    icon: React.ElementType;
    colorClass: string;
  }

  const RoutineSection: React.FC<RoutineSectionProps> = ({
    title,
    steps,
    icon: Icon,
    colorClass,
  }) => {
    if (!steps || steps.length === 0) return null;

    const arrowColorClass = colorClass.includes("orange")
      ? "text-orange-400"
      : "text-purple-400";

    return (
      <div className="mb-6 last:mb-0">
        <h4
          className={`text-sm font-bold uppercase mb-3 flex items-center ${colorClass}`}
        >
          <Icon size={16} className="mr-2" /> {title}
        </h4>
        <div className="flex overflow-x-auto pb-2 items-center space-x-0">
          {steps.map((item, index) => (
            <div
              key={item.step_number + item.product_category}
              className="flex items-center"
            >
              <RoutineStepCard
                step={item}
                openModal={() =>
                  openModal(item, routine.warnings, routine.profile)
                }
              />
              {index < steps.length - 1 && (
                <ArrowRight
                  size={24}
                  className={`mx-3 flex-shrink-0 ${arrowColorClass}`}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="w-full p-1">
      <h3 className="text-lg font-bold text-gray-100 mb-2">
        Personalized Routine: {routine.profile.skin_type} Skin
      </h3>

      {routine.warnings && routine.warnings.length > 0 && (
        <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg mb-4">
          <p className="text-xs font-semibold text-yellow-300 flex items-center">
            <AlertTriangle size={14} className="mr-1" /> View Warnings in step
            details!
          </p>
        </div>
      )}

      <RoutineSection
        title="Morning"
        steps={routine.morning_routine}
        icon={Sun}
        colorClass="text-orange-400"
      />

      <RoutineSection
        title="Evening (Double Cleanse/BHA)"
        steps={routine.evening_routine}
        icon={Moon}
        colorClass="text-purple-400"
      />

      <RoutineSection
        title="Night (Treatment/Moisture)"
        steps={routine.night_routine}
        icon={Moon}
        colorClass="text-purple-400"
      />
    </div>
  );
};
export default RoutineDisplay;
