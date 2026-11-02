import { Activity, Camera, History, MessageCircle, ShieldCheck } from "lucide-react";
import AuthButton from "./AuthButton";
import logo from "../assets/wabi-logo.png";
import type { AuthUser, Screen } from "../entities/types";

interface NavBarProps {
  screen: Screen;
  onNavigate: (screen: Screen) => void;
  authUser: AuthUser | null;
  onSignIn: (user: AuthUser) => void;
  onSignOut: () => void;
}

const NAV_ITEMS: { screen: Screen; label: string; icon: typeof Camera }[] = [
  { screen: "scan", label: "Scan", icon: Camera },
  { screen: "matches", label: "Honest picks", icon: ShieldCheck },
  { screen: "tolerance", label: "Tolerance", icon: Activity },
  { screen: "chat", label: "Chat", icon: MessageCircle },
  { screen: "history", label: "History", icon: History },
];

const NavBar: React.FC<NavBarProps> = ({ screen, onNavigate, authUser, onSignIn, onSignOut }) => {
  return (
    <nav className="flex items-center justify-between gap-2 sm:gap-4 px-3 sm:px-4 md:px-6 h-16 flex-shrink-0 bg-ink-card/60 backdrop-blur-md border-b border-white/5 z-30">
      <button
        onClick={() => onNavigate("landing")}
        className="flex items-center gap-2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 focus-visible:ring-offset-ink"
        aria-label="Go to home"
      >
        <img src={logo} alt="" aria-hidden="true" className="w-8 h-8 rounded-full" />
        <span className="text-base font-display font-semibold text-gray-100 hidden sm:inline">Wabi · Sabi</span>
      </button>

      <div className="flex items-center gap-1" role="tablist" aria-label="Sections">
        {NAV_ITEMS.map((item) => {
          const isActive = screen === item.screen;
          return (
            <button
              key={item.screen}
              role="tab"
              aria-selected={isActive}
              aria-label={item.label}
              onClick={() => onNavigate(item.screen)}
              className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-full text-sm transition ${
                isActive ? "bg-white/10 text-gray-100" : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              }`}
            >
              <item.icon size={16} aria-hidden="true" />
              <span className="hidden sm:inline">{item.label}</span>
            </button>
          );
        })}
      </div>

      <AuthButton user={authUser} onSignIn={onSignIn} onSignOut={onSignOut} />
    </nav>
  );
};

export default NavBar;
