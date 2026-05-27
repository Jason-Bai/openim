import { Button, Tooltip, Typography, message } from "antd";
import { ArrowLeft, Copy } from "lucide-react";
import type { Conversation } from "../api/openim";
import { conversationStatusText, conversationTechnicalDetail } from "../utils/conversationDisplay";

export function ConversationHeader({
  conversation,
  showBack = false,
  onBack
}: {
  conversation: Conversation;
  showBack?: boolean;
  onBack?: () => void;
}) {
  const technicalDetail = conversationTechnicalDetail(conversation);

  const copyDetail = async () => {
    try {
      await navigator.clipboard.writeText(technicalDetail);
      message.success("已复制");
    } catch {
      message.error("复制失败");
    }
  };

  return (
    <header className="chatHeader">
      {showBack && (
        <Button
          aria-label="返回会话列表"
          className="chatMobileBackButton"
          icon={<ArrowLeft size={18} />}
          onClick={onBack}
          shape="circle"
          type="text"
        />
      )}
      <div className="chatHeaderMain">
        <Typography.Title className="chatHeaderTitle" level={4}>
          {conversation.title}
        </Typography.Title>
        <Typography.Text className="chatHeaderSubtitle" type="secondary">
          {conversationStatusText(conversation)}
        </Typography.Text>
      </div>
      <div className="chatHeaderActions">
        <Tooltip title={technicalDetail}>
          <Button
            aria-label="复制会话技术信息"
            icon={<Copy size={15} />}
            onClick={copyDetail}
            size="small"
            type="text"
          />
        </Tooltip>
      </div>
    </header>
  );
}
