import { readFileSync } from "node:fs";

const apiSource = readFileSync("apps/web/src/api/openim.ts", "utf8");
const appSource = readFileSync("apps/web/src/pages/App.tsx", "utf8");

const checks = [
  {
    name: "sendConversationMessage accepts contentType parameter",
    pass: /sendConversationMessage\([^)]*contentType:\s*ConversationMessage\["content_type"\]\s*=\s*"text"/s.test(
      apiSource
    )
  },
  {
    name: "sendConversationMessage sends caller-provided content_type",
    pass: /JSON\.stringify\(\{\s*content,\s*content_type:\s*contentType\s*\}\)/s.test(apiSource)
  },
  {
    name: "submitMessage accepts optional content type",
    pass: /const submitMessage = \(value: string,\s*contentType: ConversationMessage\["content_type"\]\s*=\s*"text"\)/s.test(
      appSource
    )
  },
  {
    name: "optimistic message preserves submitted content type",
    pass: /content_type:\s*contentType/.test(appSource)
  },
  {
    name: "retry preserves previous user message content type",
    pass: /onSubmit\(lastUserMessage\.content,\s*lastUserMessage\.content_type\)/.test(appSource)
  }
];

const failed = checks.filter((check) => !check.pass);
if (failed.length) {
  console.error("Frontend code message payload regression failed:");
  for (const check of failed) {
    console.error(`- ${check.name}`);
  }
  process.exit(1);
}

console.log("Frontend code message payload regression passed.");
