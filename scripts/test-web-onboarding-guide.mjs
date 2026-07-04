import { readFileSync } from "node:fs";

const appSource = readFileSync("apps/web/src/pages/App.tsx", "utf8");
const apiSource = readFileSync("apps/web/src/api/openim.ts", "utf8");

const checks = [
  {
    name: "web API exposes direct BOT slot creation",
    pass: /export function createBot\(\s*token: string\s*\)/s.test(apiSource)
  },
  {
    name: "web API exposes direct BOT connection info retrieval",
    pass: /export function botConnectInfo\(\s*token: string,\s*botId: string\s*\)/s.test(apiSource)
  },
  {
    name: "guide shows a first-time OpenClaw assistant connect CTA",
    pass: appSource.includes("连接 OpenClaw 助手")
  },
  {
    name: "guide can create a BOT slot without sending /new-bot",
    pass: /createBotMutation = useMutation\(/.test(appSource) && /createBot\(token\)/.test(appSource)
  },
  {
    name: "successful onboarding shows BOT_ID and connection info",
    pass:
      appSource.includes("BOT_ID") &&
      appSource.includes("Gateway") &&
      appSource.includes("Token")
  },
  {
    name: "guide includes copyable plugin configuration and start-plugin instruction",
    pass:
      /navigator\.clipboard\.writeText/.test(appSource) &&
      appSource.includes("复制插件配置") &&
      appSource.includes("启动 OpenClaw 插件")
  },
  {
    name: "copyable plugin configuration includes install, version, and docs",
    pass:
      appSource.includes("pluginInstall") &&
      appSource.includes("pluginVersion") &&
      appSource.includes("pluginDocs")
  }
];

const failed = checks.filter((check) => !check.pass);
if (failed.length) {
  console.error("Frontend onboarding guide regression failed:");
  for (const check of failed) {
    console.error(`- ${check.name}`);
  }
  process.exit(1);
}

console.log("Frontend onboarding guide regression passed.");
