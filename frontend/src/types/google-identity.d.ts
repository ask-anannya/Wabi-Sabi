// Minimal shape for the Google Identity Services script (loaded at runtime
// via <script src="https://accounts.google.com/gsi/client">), just enough
// to type-check AuthButton.tsx. Not the official @types package — this app
// only uses initialize/renderButton/prompt.
interface GoogleCredentialResponse {
  credential: string;
}

interface GoogleIdConfiguration {
  client_id: string;
  callback: (response: GoogleCredentialResponse) => void;
  auto_select?: boolean;
}

interface GoogleButtonConfiguration {
  theme?: "outline" | "filled_black" | "filled_blue";
  size?: "small" | "medium" | "large";
  shape?: "rectangular" | "pill" | "circle" | "square";
  text?: "signin_with" | "signup_with" | "continue_with" | "signin";
}

interface Window {
  google?: {
    accounts: {
      id: {
        initialize: (config: GoogleIdConfiguration) => void;
        renderButton: (parent: HTMLElement, options: GoogleButtonConfiguration) => void;
        disableAutoSelect: () => void;
      };
    };
  };
}
