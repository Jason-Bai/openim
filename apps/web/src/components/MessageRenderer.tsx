import { Button, message as toast } from "antd";
import { Copy } from "lucide-react";
import type { ConversationMessage } from "../api/openim";
import { CollapsibleMessage } from "./CollapsibleMessage";
import { CopyableCodeBlock } from "./CopyableCodeBlock";
import { MessageContent } from "./MessageContent";

export function MessageRenderer({ message }: { message: ConversationMessage }) {
  if (message.content_type === "code") {
    return <CopyableCodeBlock content={message.content} />;
  }

  if (message.sender_type === "user") {
    return <div className="bubble plainBubble">{message.content}</div>;
  }

  return (
    <div className="bubble richBubble">
      <Button
        aria-label="复制消息内容"
        className="messageCopyButton"
        icon={<Copy size={14} />}
        size="small"
        type="text"
        onClick={() => copyMessageContent(message.content)}
      />
      <CollapsibleMessage>
        <MessageContent content={message.content} />
      </CollapsibleMessage>
    </div>
  );
}

async function copyMessageContent(content: string) {
  try {
    await navigator.clipboard.writeText(content);
    toast.success("已复制");
  } catch {
    toast.error("复制失败");
  }
}
