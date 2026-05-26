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

function assertContact(items, id, contactType, label) {
  const found = items.some((item) => item.id === id && item.contact_type === contactType);
  if (!found) {
    throw new Error(`${label} missing ${contactType}:${id}: ${JSON.stringify(items)}`);
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
  const info = JSON.parse(connect.content);
  if (info.bot_id !== botId || !info.token || !info.gateway_url) {
    throw new Error(`invalid connect payload: ${connect.content}`);
  }
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
  client.onMessage(async (message) => {
    await client.sendMessage({
      conversationId: message.conversationId,
      requestId: message.requestId,
      content: { type: "text", text: replyText },
    });
  });

  await client.connect();

  const bots = await get("/api/bots", token);
  const bot = bots.items.find((item) => item.bot_id === botId);
  const botConnected =
    connected && bot?.binding_status === "active" && bot?.connect_status === "connected";
  if (!botConnected) {
    throw new Error(
      `plugin connection did not bind bot: ${JSON.stringify({ connected, bot, disconnectReason })}`,
    );
  }

  const openClawConversation = await post(
    "/api/conversations/ensure",
    { target_type: "openclaw_bot", target_id: botId },
    token,
  );
  if (openClawConversation.conversation?.target_type !== "openclaw_bot") {
    throw new Error(`openclaw bot conversation missing: ${JSON.stringify(openClawConversation)}`);
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
      (item) => item.sender_type === "bot" && item.sender_id === botId && item.content === replyText,
    );
  if (!messageOk) {
    throw new Error(`plugin reply missing from send response: ${JSON.stringify(sent)}`);
  }

  const history = await get(`/api/conversations/${conversationId}/messages`, token);
  if (!history.items.some((item) => item.sender_type === "bot" && item.content === replyText)) {
    throw new Error(`plugin reply missing from history: ${JSON.stringify(history)}`);
  }

  const contacts = await get("/api/contacts", token);
  assertContact(contacts.ai, "default_bot", "system_default_bot", "contacts.ai");
  assertContact(contacts.ai, botId, "openclaw_bot", "contacts.ai");
  assertContact(contacts.all, "default_bot", "system_default_bot", "contacts.all");
  assertContact(contacts.all, botId, "openclaw_bot", "contacts.all");
  const contactsOk = true;

  await client.disconnect();

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
}

main().catch((error) => {
  console.error(error.stack ?? error.message);
  process.exit(1);
});
