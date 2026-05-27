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
      <CollapsibleMessage>
        <MessageContent content={message.content} />
      </CollapsibleMessage>
    </div>
  );
}
