import { readFileSync } from "node:fs";

const appSource = readFileSync("apps/web/src/pages/App.tsx", "utf8");

const checks = [
  {
    name: "default BOT state-changing commands are classified explicitly",
    pass: /function shouldRefreshDefaultBotState\(\s*conversation: Conversation,\s*content: string\s*\)/s.test(
      appSource
    )
  },
  {
    name: "command classifier is limited to system default BOT conversations",
    pass: /conversation\.target_type !== "system_default_bot"/.test(appSource)
  },
  {
    name: "command classifier includes BOT state-changing commands",
    pass:
      appSource.includes('"/new-bot"') &&
      appSource.includes('"/delete-bot"') &&
      appSource.includes('"/connect"') &&
      appSource.includes('"/disconnect"') &&
      appSource.includes('"/diagnose"')
  },
  {
    name: "successful matching commands invalidate contacts",
    pass:
      /shouldRefreshDefaultBotState\(data\.conversation,\s*vars\.content\)/s.test(appSource) &&
      /queryClient\.invalidateQueries\(\{\s*queryKey:\s*\["contacts"\]\s*\}\)/s.test(appSource)
  },
  {
    name: "successful sends continue to invalidate conversations",
    pass: /queryClient\.invalidateQueries\(\{\s*queryKey:\s*\["conversations"\]\s*\}\)/s.test(appSource)
  }
];

const failed = checks.filter((check) => !check.pass);
if (failed.length) {
  console.error("Frontend default BOT command refresh regression failed:");
  for (const check of failed) {
    console.error(`- ${check.name}`);
  }
  process.exit(1);
}

console.log("Frontend default BOT command refresh regression passed.");
