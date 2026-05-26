import { Button, message } from "antd";
import { Copy } from "lucide-react";

export function CopyableCodeBlock({ content }: { content: string }) {
  return (
    <div className="codeBlock">
      <Button
        className="copyButton"
        size="small"
        icon={<Copy size={14} />}
        onClick={async () => {
          await navigator.clipboard.writeText(content);
          message.success("已复制");
        }}
      />
      <pre>{content}</pre>
    </div>
  );
}

