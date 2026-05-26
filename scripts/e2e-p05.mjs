import { OpenClawBotClient } from "../packages/openclaw-bot-plugin/dist/index.js";

const api = process.env.OPENIM_API_BASE_URL ?? "http://127.0.0.1:8080";
const requestTimeoutMs = Number(process.env.OPENIM_E2E_REQUEST_TIMEOUT_MS ?? 10_000);
const globalTimeoutMs = Number(process.env.OPENIM_E2E_GLOBAL_TIMEOUT_MS ?? 90_000);

async function fetchJson(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs);
  try {
    const res = await fetch(api + path, {
      ...options,
      signal: controller.signal,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok || json.ok === false) {
      throw new Error(`${path} failed ${res.status}: ${safeJson(json)}`);
    }
    return json.data;
  } catch (error) {
    if (error?.name === "AbortError") {
      throw new Error(`${path} timed out after ${requestTimeoutMs}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

async function post(path, body, token) {
  return fetchJson(path, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
}

async function get(path, token) {
  return fetchJson(path, {
    headers: {
      ...(token ? { authorization: `Bearer ${token}` } : {}),
    },
  });
}

function safeJson(value) {
  return JSON.stringify(value, (key, item) =>
    key.toLowerCase().includes("token") ? "[redacted]" : item,
  );
}

function contactSummary(items) {
  if (!Array.isArray(items)) {
    return `type=${typeof items} value=${safeJson(items)}`;
  }
  return safeJson(items.map((item) => `${item.contact_type}:${item.id}`));
}

function assertContact(items, id, contactType, label) {
  if (!Array.isArray(items)) {
    throw new Error(`${label} must be an array, got ${contactSummary(items)}`);
  }
  const found = items.some((item) => item.id === id && item.contact_type === contactType);
  if (!found) {
    throw new Error(`${label} missing ${contactType}:${id}; present=${contactSummary(items)}`);
  }
}

async function main() {
  const suffix = Date.now();
  const username = `p05_e2e_${suffix}`;
  const password = "Password123!";
  const employeeId = `P05${suffix}`;
  const replyText = `p05 plugin reply ${suffix}`;

  await post("/api/auth/register", {
    username,
    password,
    employee_id: employeeId,
    real_name: "P05 E2E User",
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
  let info;
  try {
    info = JSON.parse(connect.content);
  } catch (error) {
    throw new Error(`/connect ${botId} did not return valid JSON`);
  }
  if (info.bot_id !== botId || !info.token || !info.gateway_url) {
    throw new Error(
      `invalid connect payload: ${safeJson({
        bot_id: info.bot_id,
        token: info.token,
        gateway_url: info.gateway_url,
      })}`,
    );
  }
  const gatewayUrl = info.gateway_url.replace("localhost", "127.0.0.1");

  let connected = false;
  let disconnectReason;
  let clientConnected = false;
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
  client.onMessage(async (message) => {
    await client.sendMessage({
      conversationId: message.conversationId,
      requestId: message.requestId,
      content: { type: "text", text: replyText },
    });
  });

  try {
    await client.connect();
    clientConnected = true;

    const bots = await get("/api/bots", token);
    const bot = bots.items.find((item) => item.bot_id === botId);
    const botConnected =
      connected && bot?.binding_status === "active" && bot?.connect_status === "connected";
    if (!botConnected) {
      throw new Error(
        `plugin connection did not bind bot: ${safeJson({ connected, bot, disconnectReason })}`,
      );
    }

    const openClawConversation = await post(
      "/api/conversations/ensure",
      { target_type: "openclaw_bot", target_id: botId },
      token,
    );
    if (openClawConversation.conversation?.target_type !== "openclaw_bot") {
      throw new Error(`openclaw bot conversation missing: ${safeJson(openClawConversation)}`);
    }
    const conversationId = openClawConversation.conversation.id;

    const sent = await post(
      `/api/conversations/${conversationId}/messages`,
      { content: "p05 smoke hello", content_type: "text" },
      token,
    );
    const responseMessages = sent.messages ?? [];
    const messageOk =
      responseMessages.some(
        (item) => item.sender_type === "user" && item.content === "p05 smoke hello",
      ) &&
      responseMessages.some(
        (item) =>
          item.sender_type === "bot" && item.sender_id === botId && item.content === replyText,
      );
    if (!messageOk) {
      throw new Error(`plugin reply missing from send response: ${safeJson(sent)}`);
    }

    const history = await get(`/api/conversations/${conversationId}/messages`, token);
    if (!history.items.some((item) => item.sender_type === "bot" && item.content === replyText)) {
      throw new Error(`plugin reply missing from history: ${safeJson(history)}`);
    }

    const contacts = await get("/api/contacts", token);
    assertContact(contacts.ai, "default_bot", "system_default_bot", "contacts.ai");
    assertContact(contacts.ai, botId, "openclaw_bot", "contacts.ai");
    assertContact(contacts.all, "default_bot", "system_default_bot", "contacts.all");
    assertContact(contacts.all, botId, "openclaw_bot", "contacts.all");
    const contactsOk = true;

    console.log(
      JSON.stringify(
        {
          ok: true,
          contactsOk,
          messageOk,
          botConnected,
          username,
          employeeId,
          botId,
          conversationId,
          gatewayUrl: info.gateway_url,
        },
        null,
        2,
      ),
    );
  } finally {
    if (clientConnected) {
      await client.disconnect();
    }
  }
}

let globalTimer;
await Promise.race([
  main(),
  new Promise((_, reject) => {
    globalTimer = setTimeout(
      () => reject(new Error(`e2e:p05 timed out after ${globalTimeoutMs}ms`)),
      globalTimeoutMs,
    );
  }),
])
  .finally(() => {
    clearTimeout(globalTimer);
  })
  .catch((error) => {
  console.error(error.stack ?? error.message);
  process.exit(1);
});
