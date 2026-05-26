import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { OpenClawBotClient } from "../packages/openclaw-bot-plugin/dist/index.js";

const execFileAsync = promisify(execFile);
const api = process.env.OPENIM_API_BASE_URL ?? "http://127.0.0.1:8080";
const username = process.env.OPENIM_USERNAME;
const password = process.env.OPENIM_PASSWORD ?? "Password123!";
const existingBotId = process.env.OPENIM_BOT_ID;
const openclawCli = process.env.OPENCLAW_CLI ?? "openclaw";

if (!username) {
  console.error("OPENIM_USERNAME is required");
  process.exit(1);
}

async function post(path, body, token) {
  const res = await fetch(api + path, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.ok === false) {
    throw new Error(`${path} failed ${res.status}: ${JSON.stringify(json)}`);
  }
  return json.data;
}

async function getConnectPayload(token, botId) {
  const first = await post("/api/default-bot/commands", { command: `/connect ${botId}` }, token);
  if (first.reply_type === "code") {
    return JSON.parse(first.content);
  }
  if (first.content.includes(`confirm regenerate ${botId}`)) {
    const regenerated = await post(
      "/api/default-bot/commands",
      { command: `confirm regenerate ${botId}` },
      token,
    );
    return JSON.parse(regenerated.content);
  }
  throw new Error(`Cannot get connect payload: ${first.content}`);
}

async function getOrCreateBot(token) {
  if (existingBotId) {
    return existingBotId;
  }
  const newBot = await post("/api/default-bot/commands", { command: "/new-bot" }, token);
  const botId = newBot.content.match(/BOT_ID: (bot_[A-Z0-9]+)/)?.[1];
  if (!botId) {
    throw new Error(`BOT_ID not found: ${newBot.content}`);
  }
  return botId;
}

async function askOpenClaw(message) {
  const { stdout } = await execFileAsync(
    openclawCli,
    [
      "agent",
      "--agent",
      "main",
      "--session-id",
      "openim-openclaw-assistant",
      "--message",
      message,
      "--json",
      "--timeout",
      "120",
    ],
    { maxBuffer: 1024 * 1024 * 8 },
  );
  const result = JSON.parse(stdout);
  const text = result.result?.payloads?.[0]?.text;
  if (result.status !== "ok" || typeof text !== "string") {
    throw new Error(`OpenClaw agent failed: ${stdout}`);
  }
  return text;
}

async function main() {
  const login = await post("/api/auth/login", { username, password });
  const token = login.access_token;
  const botId = await getOrCreateBot(token);
  const payload = await getConnectPayload(token, botId);
  const gatewayUrl = payload.gateway_url.replace("localhost", "127.0.0.1");

  const client = new OpenClawBotClient({
    botId,
    token: payload.token,
    gatewayUrl,
    heartbeatIntervalMs: 1000,
  });

  client.onMessage(async (message) => {
    try {
      const text = message.content.type === "text" ? message.content.text : JSON.stringify(message.content.data);
      const reply = await askOpenClaw(text);
      await client.sendMessage({
        conversationId: message.conversationId,
        requestId: message.requestId,
        content: { type: "text", text: reply },
      });
    } catch (error) {
      await client.sendMessage({
        conversationId: message.conversationId,
        requestId: message.requestId,
        content: { type: "text", text: `OpenClaw 调用失败：${error.message ?? String(error)}` },
      });
    }
  });

  client.onConnected(() => {
    console.log(
      JSON.stringify(
        {
          ready: true,
          username,
          botId,
          gatewayUrl: payload.gateway_url,
          openclawSession: "openim-openclaw-assistant",
        },
        null,
        2,
      ),
    );
  });

  client.onDisconnected((reason) => {
    console.log(JSON.stringify({ disconnected: true, reason }, null, 2));
  });

  await client.connect();
  setInterval(() => {}, 60_000);
}

main().catch((error) => {
  console.error(error.stack ?? error.message);
  process.exit(1);
});
