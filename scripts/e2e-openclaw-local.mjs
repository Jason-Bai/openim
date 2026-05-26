import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { OpenClawBotClient } from "../packages/openclaw-bot-plugin/dist/index.js";

const execFileAsync = promisify(execFile);
const openimApi = process.env.OPENIM_API_BASE_URL ?? "http://127.0.0.1:8080";
const openclawControlUrl = process.env.OPENCLAW_CONTROL_URL ?? "http://127.0.0.1:18789";
const openclawCli = process.env.OPENCLAW_CLI ?? "openclaw";

async function post(path, body, token) {
  const res = await fetch(openimApi + path, {
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

async function get(path, token) {
  const res = await fetch(openimApi + path, {
    headers: {
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.ok === false) {
    throw new Error(`${path} failed ${res.status}: ${JSON.stringify(json)}`);
  }
  return json.data;
}

async function assertOpenClawControlReachable() {
  const res = await fetch(openclawControlUrl);
  const html = await res.text();
  if (!res.ok || !html.includes("OpenClaw Control")) {
    throw new Error(`OpenClaw Control is not reachable at ${openclawControlUrl}`);
  }
}

async function assertOpenClawGatewayReachable() {
  const { stdout } = await execFileAsync(
    openclawCli,
    ["gateway", "call", "health", "--json"],
    { maxBuffer: 1024 * 1024 * 4 },
  );
  const health = JSON.parse(stdout);
  if (!health.ok) {
    throw new Error(`OpenClaw gateway health failed: ${stdout}`);
  }
  return {
    ok: health.ok,
    pluginCount: health.plugins?.loaded?.length ?? 0,
    eventLoopDegraded: Boolean(health.eventLoop?.degraded),
  };
}

async function maybeRunOpenClawAgentSmoke() {
  if (process.env.OPENCLAW_AGENT_SMOKE !== "1") {
    return { skipped: true };
  }
  const { stdout } = await execFileAsync(
    openclawCli,
    [
      "agent",
      "--agent",
      "main",
      "--session-id",
      "openim-p0-local",
      "--message",
      "OpenIM P0 smoke: 请只回复 OK_OPENCLAW_READY",
      "--json",
      "--timeout",
      "60",
    ],
    { maxBuffer: 1024 * 1024 * 8 },
  );
  const result = JSON.parse(stdout);
  const text = result.result?.payloads?.[0]?.text ?? "";
  if (result.status !== "ok" || !text.includes("OK_OPENCLAW_READY")) {
    throw new Error(`OpenClaw agent smoke failed: ${stdout}`);
  }
  return { skipped: false, status: result.status, text };
}

async function main() {
  await assertOpenClawControlReachable();
  const openclawGateway = await assertOpenClawGatewayReachable();
  const openclawAgent = await maybeRunOpenClawAgentSmoke();

  const suffix = Date.now();
  const username = `openclaw_e2e_${suffix}`;
  const password = "Password123!";
  const employeeId = `OPENCLAW${suffix}`;

  await post("/api/auth/register", {
    username,
    password,
    employee_id: employeeId,
    real_name: "OpenClaw Local E2E 用户",
  });
  const login = await post("/api/auth/login", { username, password });
  const token = login.access_token;

  const newBot = await post("/api/default-bot/commands", { command: "/new-bot" }, token);
  const match = newBot.content.match(/BOT_ID: (bot_[A-Z0-9]+)/);
  if (!match) {
    throw new Error(`BOT_ID not found in reply: ${newBot.content}`);
  }
  const botId = match[1];

  const connect = await post("/api/default-bot/commands", { command: `/connect ${botId}` }, token);
  const info = JSON.parse(connect.content);
  const gatewayUrl = info.gateway_url.replace("localhost", "127.0.0.1");

  let connected = false;
  const client = new OpenClawBotClient({
    botId,
    token: info.token,
    gatewayUrl,
    autoReconnect: false,
    heartbeatIntervalMs: 1000,
  });
  client.onConnected(() => {
    connected = true;
  });

  await client.connect();

  const bots = await get("/api/bots", token);
  const bot = bots.items.find((item) => item.bot_id === botId);
  if (!connected || !bot || bot.binding_status !== "active" || bot.connect_status !== "connected") {
    throw new Error(`OpenClaw local binding failed: ${JSON.stringify({ connected, bot })}`);
  }

  await client.disconnect();

  console.log(
    JSON.stringify(
      {
        ok: true,
        openclaw: {
          controlUrl: openclawControlUrl,
          gateway: openclawGateway,
          agent: openclawAgent,
        },
        openim: {
          username,
          employeeId,
          botId,
          gatewayUrl: info.gateway_url,
          bindingStatus: bot.binding_status,
          connectStatus: bot.connect_status,
        },
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error.stack ?? error.message);
  process.exit(1);
});
