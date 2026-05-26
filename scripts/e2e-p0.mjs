import WebSocket from "isomorphic-ws";

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

function waitFor(ws, type, timeoutMs = 5000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`timeout waiting for ${type}`)), timeoutMs);
    function onMessage(raw) {
      const message = JSON.parse(raw.toString());
      if (message.type === type) {
        clearTimeout(timer);
        ws.off("message", onMessage);
        resolve(message);
      }
    }
    ws.on("message", onMessage);
  });
}

async function main() {
  const suffix = Date.now();
  const username = `e2e_${suffix}`;
  const password = "Password123!";
  const employeeId = `EMP${suffix}`;

  await post("/api/auth/register", {
    username,
    password,
    employee_id: employeeId,
    real_name: "E2E 用户",
  });
  const login = await post("/api/auth/login", { username, password });
  const token = login.access_token;

  const defaultConversation = await post(
    "/api/conversations/ensure",
    { target_type: "system_default_bot", target_id: "default_bot" },
    token,
  );
  if (defaultConversation.conversation?.target_type !== "system_default_bot") {
    throw new Error(`default bot conversation missing: ${JSON.stringify(defaultConversation)}`);
  }

  const newBot = await post("/api/default-bot/commands", { command: "/new-bot" }, token);
  const match = newBot.content.match(/BOT_ID: (bot_[A-Z0-9]+)/);
  if (!match) {
    throw new Error(`BOT_ID not found in reply: ${newBot.content}`);
  }
  const botId = match[1];

  const connect = await post("/api/default-bot/commands", { command: `/connect ${botId}` }, token);
  const info = JSON.parse(connect.content);
  const gatewayUrl = info.gateway_url.replace("localhost", "127.0.0.1");

  const ws = new WebSocket(gatewayUrl);
  await new Promise((resolve, reject) => {
    ws.once("open", resolve);
    ws.once("error", reject);
  });

  ws.send(JSON.stringify({ type: "auth", request_id: "req-auth-1", bot_id: botId, token: info.token }));
  const auth = await waitFor(ws, "auth.result");
  if (!auth.ok) {
    throw new Error(`auth failed: ${JSON.stringify(auth)}`);
  }

  ws.send(
    JSON.stringify({
      type: "handshake",
      request_id: "req-handshake-1",
      plugin_name: "@openim/openclaw-bot-plugin",
      plugin_version: "0.1.0",
    }),
  );
  const handshake = await waitFor(ws, "handshake.result");
  if (!handshake.ok) {
    throw new Error(`handshake failed: ${JSON.stringify(handshake)}`);
  }

  ws.send(JSON.stringify({ type: "heartbeat", request_id: "req-heartbeat-1" }));
  const heartbeat = await waitFor(ws, "heartbeat.result");
  if (!heartbeat.ok) {
    throw new Error(`heartbeat failed: ${JSON.stringify(heartbeat)}`);
  }

  const bots = await get("/api/bots", token);
  const bot = bots.items.find((item) => item.bot_id === botId);
  if (!bot || bot.binding_status !== "active" || bot.connect_status !== "connected") {
    throw new Error(`bot binding not active while connected: ${JSON.stringify(bot)}`);
  }

  ws.close();

  console.log(
    JSON.stringify(
      {
        ok: true,
        username,
        employeeId,
        botId,
        gatewayUrl: info.gateway_url,
        auth: auth.ok,
        handshake: handshake.ok,
        heartbeat: heartbeat.ok,
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
