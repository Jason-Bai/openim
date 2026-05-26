import WebSocket from "isomorphic-ws";

export type DisconnectReason = {
  code:
    | "CLIENT_DISCONNECT"
    | "SERVER_DISCONNECT"
    | "NETWORK_ERROR"
    | "HEARTBEAT_TIMEOUT"
    | "AUTH_TIMEOUT"
    | "AUTH_FAILED"
    | "BOT_REVOKED"
    | "TOKEN_REGENERATED";
  message: string;
  retryable: boolean;
};

export type BotPluginLogger = {
  debug?: (message: string, meta?: Record<string, unknown>) => void;
  info?: (message: string, meta?: Record<string, unknown>) => void;
  warn?: (message: string, meta?: Record<string, unknown>) => void;
  error?: (message: string, meta?: Record<string, unknown>) => void;
};

export type BotPluginError = Error & {
  code: string;
  retryable: boolean;
};

export type BotInboundMessage = {
  messageId: string;
  conversationId: string;
  from: { type: "user" | "system"; id: string };
  content: { type: "text"; text: string } | { type: "json"; data: unknown };
  createdAt: string;
  requestId: string;
};

export type SendMessageInput = {
  conversationId: string;
  content: { type: "text"; text: string } | { type: "json"; data: unknown };
  requestId?: string;
};

export type SendMessageResult = {
  ok: boolean;
  messageId?: string;
  requestId: string;
  error?: BotPluginError;
};

export type OpenClawBotClientOptions = {
  botId: string;
  token: string;
  gatewayUrl: string;
  protocolVersion?: "bot-v1";
  autoReconnect?: boolean;
  heartbeatIntervalMs?: number;
  logger?: BotPluginLogger;
};

type ClientState =
  | "idle"
  | "connecting"
  | "authenticating"
  | "handshaking"
  | "connected"
  | "disconnected";

type ProtocolMessage = {
  type: string;
  request_id?: string;
  protocol_version?: string;
  ok?: boolean;
  error?: { code: string; message: string; retryable: boolean };
  reason?: { code: DisconnectReason["code"]; message: string; retryable: boolean };
  [key: string]: unknown;
};

export class OpenClawBotClient {
  private readonly options: Required<Omit<OpenClawBotClientOptions, "logger">> & {
    logger?: BotPluginLogger;
  };
  private ws?: WebSocket;
  private heartbeat?: ReturnType<typeof setInterval>;
  private reconnectAttempt = 0;
  private manualDisconnect = false;
  private state: ClientState = "idle";
  private connectedHandlers: Array<() => void> = [];
  private disconnectedHandlers: Array<(reason: DisconnectReason) => void> = [];
  private errorHandlers: Array<(error: BotPluginError) => void> = [];
  private messageHandlers: Array<(message: BotInboundMessage) => Promise<void> | void> = [];
  private pendingSends = new Map<
    string,
    { resolve: (result: SendMessageResult) => void; reject: (error: BotPluginError) => void }
  >();

  constructor(options: OpenClawBotClientOptions) {
    this.options = {
      protocolVersion: "bot-v1",
      autoReconnect: true,
      heartbeatIntervalMs: 30_000,
      ...options
    };
  }

  async connect(): Promise<void> {
    this.manualDisconnect = false;
    this.state = "connecting";
    await this.openSocket();
  }

  async disconnect(): Promise<void> {
    this.manualDisconnect = true;
    this.stopHeartbeat();
    this.ws?.close(1000, "CLIENT_DISCONNECT");
    this.state = "disconnected";
  }

  onConnected(handler: () => void): void {
    this.connectedHandlers.push(handler);
  }

  onDisconnected(handler: (reason: DisconnectReason) => void): void {
    this.disconnectedHandlers.push(handler);
  }

  onMessage(handler: (message: BotInboundMessage) => Promise<void> | void): void {
    this.messageHandlers.push(handler);
  }

  onError(handler: (error: BotPluginError) => void): void {
    this.errorHandlers.push(handler);
  }

  async sendMessage(input: SendMessageInput): Promise<SendMessageResult> {
    const requestId = input.requestId ?? this.requestId("send");
    return new Promise((resolve, reject) => {
      this.pendingSends.set(requestId, { resolve, reject });
      this.send({
        type: "send_message",
        request_id: requestId,
        protocol_version: this.options.protocolVersion,
        bot_id: this.options.botId,
        conversation_id: input.conversationId,
        content: input.content
      });
      setTimeout(() => {
        if (!this.pendingSends.has(requestId)) return;
        this.pendingSends.delete(requestId);
        reject(this.toError("MESSAGE_SEND_FAILED", "sendMessage timed out", true));
      }, 30_000);
    });
  }

  private openSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.options.gatewayUrl);
      this.ws = ws;

      ws.onopen = () => {
        this.state = "authenticating";
        this.send({
          type: "auth",
          request_id: this.requestId("auth"),
          protocol_version: this.options.protocolVersion,
          bot_id: this.options.botId,
          token: this.options.token
        });
      };

      ws.onmessage = async (event) => {
        try {
          const message = JSON.parse(event.data.toString()) as ProtocolMessage;
          await this.handleProtocolMessage(message, resolve, reject);
        } catch (error) {
          const wrapped = this.toError("MESSAGE_FORMAT_INVALID", String(error), false);
          this.emitError(wrapped);
          reject(wrapped);
        }
      };

      ws.onerror = () => {
        const error = this.toError("NETWORK_ERROR", "WebSocket network error", true);
        this.emitError(error);
        reject(error);
      };

      ws.onclose = (event) => {
        this.stopHeartbeat();
        const reason = this.closeReason(event.code, event.reason);
        this.state = "disconnected";
        this.disconnectedHandlers.forEach((handler) => handler(reason));
        if (!this.manualDisconnect && this.options.autoReconnect && reason.retryable) {
          this.scheduleReconnect();
        }
      };
    });
  }

  private async handleProtocolMessage(
    message: ProtocolMessage,
    resolve: () => void,
    reject: (reason?: unknown) => void
  ): Promise<void> {
    if (message.type === "auth.result") {
      if (!message.ok) {
        const error = this.toError(
          message.error?.code ?? "AUTH_FAILED",
          message.error?.message ?? "Auth failed",
          false
        );
        this.emitError(error);
        reject(error);
        return;
      }
      this.state = "handshaking";
      this.send({
        type: "handshake",
        request_id: this.requestId("handshake"),
        protocol_version: this.options.protocolVersion,
        bot_id: this.options.botId,
        runtime: { name: "@openim/openclaw-bot-plugin", version: "0.1.0" }
      });
      return;
    }

    if (message.type === "handshake.result") {
      if (!message.ok) {
        const error = this.toError(
          message.error?.code ?? "HANDSHAKE_FAILED",
          message.error?.message ?? "Handshake failed",
          false
        );
        this.emitError(error);
        reject(error);
        return;
      }
      this.state = "connected";
      this.reconnectAttempt = 0;
      this.startHeartbeat();
      this.connectedHandlers.forEach((handler) => handler());
      resolve();
      return;
    }

    if (message.type === "server.disconnect") {
      const reason = message.reason ?? {
        code: "SERVER_DISCONNECT",
        message: "Server disconnected",
        retryable: false
      };
      this.ws?.close(reason.code === "TOKEN_REGENERATED" ? 4001 : 4000, reason.code);
      return;
    }

    if (message.type === "inbound_message") {
      const inbound = this.toInboundMessage(message);
      await Promise.all(this.messageHandlers.map((handler) => handler(inbound)));
      return;
    }

    if (message.type === "send_message.result") {
      const requestId = String(message.request_id);
      const pending = this.pendingSends.get(requestId);
      if (!pending) return;
      this.pendingSends.delete(requestId);
      if (!message.ok) {
        const error = this.toError(
          message.error?.code ?? "MESSAGE_SEND_FAILED",
          message.error?.message ?? "Send message failed",
          message.error?.retryable ?? true
        );
        pending.reject(error);
        return;
      }
      pending.resolve({ ok: true, requestId });
    }
  }

  private send(payload: Record<string, unknown>): void {
    this.ws?.send(JSON.stringify(payload));
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeat = setInterval(() => {
      this.send({
        type: "heartbeat",
        request_id: this.requestId("heartbeat"),
        protocol_version: this.options.protocolVersion,
        bot_id: this.options.botId
      });
    }, this.options.heartbeatIntervalMs);
  }

  private stopHeartbeat(): void {
    if (this.heartbeat) {
      clearInterval(this.heartbeat);
      this.heartbeat = undefined;
    }
  }

  private scheduleReconnect(): void {
    this.reconnectAttempt += 1;
    const baseDelay = Math.min(30_000, 1000 * 2 ** (this.reconnectAttempt - 1));
    const jitter = Math.floor(Math.random() * 250);
    setTimeout(() => void this.openSocket(), baseDelay + jitter);
  }

  private closeReason(code: number, reason: string): DisconnectReason {
    if (this.manualDisconnect) {
      return { code: "CLIENT_DISCONNECT", message: "Client disconnected", retryable: false };
    }
    if (code === 4001 || reason === "TOKEN_REGENERATED") {
      return { code: "TOKEN_REGENERATED", message: "Token regenerated", retryable: false };
    }
    if (reason === "AUTH_TIMEOUT") {
      return { code: "AUTH_TIMEOUT", message: "Auth timeout", retryable: false };
    }
    if (reason === "AUTH_FAILED") {
      return { code: "AUTH_FAILED", message: "Auth failed", retryable: false };
    }
    return { code: "NETWORK_ERROR", message: "Network disconnected", retryable: true };
  }

  private toInboundMessage(message: ProtocolMessage): BotInboundMessage {
    return {
      messageId: String(message.message_id),
      conversationId: String(message.conversation_id),
      from: message.from as BotInboundMessage["from"],
      content: message.content as BotInboundMessage["content"],
      createdAt: String(message.created_at),
      requestId: String(message.request_id)
    };
  }

  private requestId(prefix: string): string {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2)}`;
  }

  private toError(code: string, message: string, retryable: boolean): BotPluginError {
    const error = new Error(message) as BotPluginError;
    error.code = code;
    error.retryable = retryable;
    return error;
  }

  private emitError(error: BotPluginError): void {
    this.options.logger?.error?.(error.message, { code: error.code, retryable: error.retryable });
    this.errorHandlers.forEach((handler) => handler(error));
  }
}

export default OpenClawBotClient;
