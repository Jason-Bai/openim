import { OpenClawBotClient } from "../packages/openclaw-bot-plugin/dist/index.js";

const api = process.env.OPENIM_API_BASE_URL ?? "http://127.0.0.1:8080";

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

async function get(path, token) {
  const res = await fetch(api + path, {
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

async function main() {
  const suffix = Date.now();
  const username = `plugin_e2e_${suffix}`;
  const password = "Password123!";
  const employeeId = `PLUGIN${suffix}`;

  await post("/api/auth/register", {
    username,
    password,
    employee_id: employeeId,
    real_name: "Plugin E2E 用户",
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
  let disconnectReason;
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
  client.onDisconnected((reason) => {
    disconnectReason = reason;
  });

  await client.connect();

  const bots = await get("/api/bots", token);
  const bot = bots.items.find((item) => item.bot_id === botId);
  if (!connected || !bot || bot.binding_status !== "active" || bot.connect_status !== "connected") {
    throw new Error(
      `plugin connection did not bind bot: ${JSON.stringify({ connected, bot, disconnectReason })}`,
    );
  }

  await client.disconnect();

  console.log(
    JSON.stringify(
      {
        ok: true,
        via: "@openim/openclaw-bot-plugin",
        username,
        employeeId,
        botId,
        gatewayUrl: info.gateway_url,
        bindingStatus: bot.binding_status,
        connectStatus: bot.connect_status,
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
