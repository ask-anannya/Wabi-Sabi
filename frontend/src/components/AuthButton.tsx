import { useEffect, useRef, useState } from "react";
import { LogOut, UserRound } from "lucide-react";
import { signInWithGoogle } from "../services/api";
import type { AuthUser } from "../entities/types";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined;
const GIS_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

interface AuthButtonProps {
  user: AuthUser | null;
  onSignIn: (user: AuthUser) => void;
  onSignOut: () => void;
}

function loadGoogleScript(onLoad: () => void) {
  const existing = document.querySelector(`script[src="${GIS_SCRIPT_SRC}"]`);
  if (existing) {
    onLoad();
    return;
  }
  const script = document.createElement("script");
  script.src = GIS_SCRIPT_SRC;
  script.async = true;
  script.defer = true;
  script.onload = onLoad;
  document.head.appendChild(script);
}

const AuthButton: React.FC<AuthButtonProps> = ({ user, onSignIn, onSignOut }) => {
  const buttonSlotRef = useRef<HTMLDivElement>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [signInError, setSignInError] = useState<string | null>(null);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || user) return;

    loadGoogleScript(() => {
      if (!window.google || !buttonSlotRef.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          try {
            const signedInUser = await signInWithGoogle(response.credential);
            onSignIn(signedInUser);
          } catch {
            setSignInError("Sign-in failed. Please try again.");
          }
        },
      });
      // Icon-only on phones: the full "Sign in with Google" pill doesn't fit
      // beside five nav tabs at 390px.
      const narrow = window.matchMedia("(max-width: 639px)").matches;
      window.google.accounts.id.renderButton(buttonSlotRef.current, {
        type: narrow ? "icon" : "standard",
        theme: "filled_black",
        size: "medium",
        shape: narrow ? "circle" : "pill",
      });
    });
  }, [user, onSignIn]);

  if (!GOOGLE_CLIENT_ID) {
    return (
      <span
        title="Google sign-in isn't configured on this deployment yet"
        className="text-xs text-gray-600 px-3 py-1.5 rounded-full border border-white/10"
      >
        Sign-in unavailable
      </span>
    );
  }

  if (user) {
    return (
      <div className="relative">
        <button
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-haspopup="true"
          aria-expanded={menuOpen}
          className="flex items-center gap-2 rounded-full pl-1 pr-3 py-1 bg-white/5 border border-white/10 hover:bg-white/10 transition"
        >
          {user.picture ? (
            <img src={user.picture} alt="" aria-hidden="true" className="w-7 h-7 rounded-full" />
          ) : (
            <span className="w-7 h-7 rounded-full bg-brand-500 flex items-center justify-center">
              <UserRound size={14} className="text-white" aria-hidden="true" />
            </span>
          )}
          <span className="text-sm text-gray-200 max-w-[8rem] truncate">{user.name ?? user.email}</span>
        </button>

        {menuOpen && (
          <div className="absolute right-0 mt-2 w-48 rounded-xl bg-ink-card border border-white/10 shadow-lift py-1 z-40">
            <p className="px-3 py-2 text-xs text-gray-500 truncate border-b border-white/5">{user.email}</p>
            <button
              onClick={() => {
                setMenuOpen(false);
                onSignOut();
              }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-200 hover:bg-white/5 transition"
            >
              <LogOut size={14} aria-hidden="true" /> Sign out
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div ref={buttonSlotRef} />
      {signInError && (
        <p role="alert" className="text-xs text-rose-400">
          {signInError}
        </p>
      )}
    </div>
  );
};

export default AuthButton;
