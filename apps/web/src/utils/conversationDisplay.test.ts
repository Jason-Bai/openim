import { describe, expect, it } from "vitest";
import type { Conversation } from "../api/openim";
import {
  conversationStatusText,
  conversationTechnicalDetail,
  formatConversationPreview
} from "./conversationDisplay";

describe("conversation display helpers", () => {
  it("formats markdown-rich message previews as concise plain text", () => {
    const content = `# 长消息折叠 QA

## 一、背景
- [ ] 梳理需求
- [x] 编写代码

\`\`\`ts
const status = "ready";
\`\`\`

| 项目 | 结果 |
| --- | --- |
| Markdown | 通过 |

[OpenClaw 工作区](./)`;

    expect(formatConversationPreview(content)).toBe(
      "长消息折叠 QA 一、背景 梳理需求 编写代码 代码片段 项目 结果 Markdown 通过 OpenClaw 工作区"
    );
  });

  it("returns an empty-state preview when no message exists", () => {
    expect(formatConversationPreview(null)).toBe("暂无消息");
  });

  it("shows business-facing status before technical ids", () => {
    const conversation: Conversation = {
      id: "conversation_1",
      conversation_type: "direct",
      target_type: "openclaw_bot",
      target_id: "bot_abc",
      title: "OpenClaw 员工助手",
      last_message: null,
      last_message_id: null,
      last_message_at: null,
      online: true
    };

    expect(conversationStatusText(conversation)).toBe("OpenClaw assistant · Connected");
    expect(conversationTechnicalDetail(conversation)).toBe("BOT_ID: bot_abc");
  });
});
