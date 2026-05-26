import { create } from "zustand";
import type { User } from "../api/openim";

type AuthState = {
  token: string | null;
  user: User | null;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
};

const savedToken = localStorage.getItem("openim_token");
const savedUser = localStorage.getItem("openim_user");

export const useAuthStore = create<AuthState>((set) => ({
  token: savedToken,
  user: savedUser ? (JSON.parse(savedUser) as User) : null,
  setAuth: (token, user) => {
    localStorage.setItem("openim_token", token);
    localStorage.setItem("openim_user", JSON.stringify(user));
    set({ token, user });
  },
  clearAuth: () => {
    localStorage.removeItem("openim_token");
    localStorage.removeItem("openim_user");
    set({ token: null, user: null });
  }
}));

