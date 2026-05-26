import { api } from "./client";

export type User = {
  id: number;
  username: string;
  employee_id: string;
  real_name: string;
  contact_type?: "user";
  relationship: "self" | "friend" | "none" | "pending_out" | "pending_in";
  online: boolean;
  last_seen_at: string | null;
};

export type BotItem = {
  bot_id: string;
  name: string;
  bot_type: string;
  connect_status: string;
  binding_status: string;
  last_seen_at: string | null;
  first_connected_at: string | null;
};

export type BotStatusChangedEvent = {
  type: "bot.status_changed";
  bot: BotItem;
};

export type ContactItem =
  | {
      id: "default_bot";
      contact_type: "system_default_bot";
      title: string;
      subtitle: string;
      online: boolean;
    }
  | {
      id: string;
      contact_type: "openclaw_bot";
      title: string;
      subtitle: string;
      online: boolean;
      bot: BotItem;
    }
  | {
      id: string;
      contact_type: "user";
      title: string;
      subtitle: string;
      online: boolean;
      user: User;
    };

export type Conversation = {
  id: string;
  conversation_type: string;
  target_type: string;
  target_id: string;
  title: string;
  last_message: string | null;
  last_message_id: string | null;
  last_message_at: string | null;
  online: boolean;
};

export type ConversationMessage = {
  id: string;
  conversation_id: string;
  sender_type: "user" | "bot" | "system";
  sender_id: string;
  content_type: "text" | "code";
  content: string;
  status: string;
  created_at: string;
  client_message_id: string | null;
};

export type LoginData = {
  access_token: string;
  token_type: "Bearer";
  user: User;
};

export type BotReply = {
  reply_type: "text" | "code";
  content: string;
};

export function register(input: {
  username: string;
  password: string;
  employee_id: string;
  real_name: string;
}) {
  return api<{ user: User }>("/auth/register", { method: "POST", body: JSON.stringify(input) });
}

export function login(input: { username: string; password: string }) {
  return api<LoginData>("/auth/login", { method: "POST", body: JSON.stringify(input) });
}

export function me(token: string) {
  return api<{ user: User }>("/auth/me", {}, token);
}

export function users(token: string) {
  return api<{ items: User[] }>("/users", {}, token);
}

export function contacts(token: string) {
  return api<{ ai: ContactItem[]; all: ContactItem[] }>("/contacts", {}, token);
}

export function addFriend(token: string, userId: number) {
  return api<{ relationship: User["relationship"] }>(
    `/friends/${userId}`,
    { method: "POST" },
    token
  );
}

export function acceptFriend(token: string, userId: number) {
  return api<{ relationship: User["relationship"] }>(
    `/friends/${userId}/accept`,
    { method: "POST" },
    token
  );
}

export function rejectFriend(token: string, userId: number) {
  return api<{ relationship: User["relationship"] }>(
    `/friends/${userId}/reject`,
    { method: "POST" },
    token
  );
}

export function bots(token: string) {
  return api<{ items: BotItem[] }>("/bots", {}, token);
}

export function conversations(token: string) {
  return api<{ items: Conversation[] }>("/conversations", {}, token);
}

export function ensureConversation(token: string, targetType: string, targetId: string) {
  return api<{ conversation: Conversation; created: boolean; initial_messages: ConversationMessage[] }>(
    "/conversations/ensure",
    { method: "POST", body: JSON.stringify({ target_type: targetType, target_id: targetId }) },
    token
  );
}

export function conversationMessages(token: string, conversationId: string) {
  return api<{ items: ConversationMessage[]; has_more: boolean; next_before: string | null }>(
    `/conversations/${conversationId}/messages`,
    {},
    token
  );
}

export function sendConversationMessage(token: string, conversationId: string, content: string) {
  return api<{ conversation: Conversation; messages: ConversationMessage[] }>(
    `/conversations/${conversationId}/messages`,
    { method: "POST", body: JSON.stringify({ content, content_type: "text" }) },
    token
  );
}

export function defaultBotCommand(token: string, command: string, conversationId?: string) {
  return api<BotReply>(
    "/default-bot/commands",
    { method: "POST", body: JSON.stringify({ command, conversation_id: conversationId }) },
    token
  );
}

export function sendBotMessage(token: string, botId: string, text: string) {
  return api<{ reply: { content: string; request_id: string } }>(
    `/bots/${botId}/messages`,
    { method: "POST", body: JSON.stringify({ text }) },
    token
  );
}
