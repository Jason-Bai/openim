import type { Conversation } from "../api/openim";

const MAX_PREVIEW_LENGTH = 80;

export function formatConversationPreview(value?: string | null) {
  const plain = markdownToPlainText(value || "");
  if (!plain) return "暂无消息";
  return plain.length > MAX_PREVIEW_LENGTH ? `${plain.slice(0, MAX_PREVIEW_LENGTH)}...` : plain;
}

export function conversationStatusText(conversation: Conversation) {
  if (conversation.target_type === "system_default_bot") return "System assistant · Online";
  if (conversation.target_type === "openclaw_bot") {
    return conversation.online ? "OpenClaw assistant · Connected" : "OpenClaw assistant · Disconnected";
  }
  return conversation.online ? "Direct message · Online" : "Direct message · Offline";
}

export function conversationTechnicalDetail(conversation: Conversation) {
  if (conversation.target_type === "openclaw_bot") return `BOT_ID: ${conversation.target_id}`;
  if (conversation.target_type === "system_default_bot") return `Target: ${conversation.target_id}`;
  return `User ID: ${conversation.target_id}`;
}

function markdownToPlainText(value: string) {
  return value
    .replace(/```[\s\S]*?```/g, "代码片段")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*]\s+\[[ xX]\]\s+/gm, "")
    .replace(/^\s*[-*]\s+/gm, "")
    .replace(/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/gm, " ")
    .replace(/[>*_`~]/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\s*\|\s*/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}
