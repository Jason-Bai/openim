import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Button, Form, Input, List, Segmented, Typography, message } from "antd";
import { Bot, LogOut, Send, UserRound, UsersRound } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import {
  BotItem,
  ContactItem,
  Conversation,
  ConversationMessage,
  User,
  addFriend,
  contacts,
  conversationMessages,
  conversations,
  ensureConversation,
  login,
  register,
  sendConversationMessage,
} from "../api/openim";
import { CopyableCodeBlock } from "../components/CopyableCodeBlock";
import { useAuthStore } from "../state/authStore";

type MenuKey = "sessions" | "contacts";
type ProfileTarget =
  | { type: "system_default_bot"; id: "default_bot" }
  | { type: "openclaw_bot"; bot: BotItem }
  | { type: "user"; user: User };
type SelectedView =
  | { type: "guide" }
  | { type: "profile"; target: ProfileTarget }
  | { type: "conversation"; conversationId: string };

type MessagePage = {
  items: ConversationMessage[];
  has_more: boolean;
  next_before: string | null;
};

export function App() {
  const { token, user, setAuth, clearAuth } = useAuthStore();
  if (!token || !user) {
    return <LoginPage onAuthed={setAuth} />;
  }
  return <ChatPage token={token} username={user.username} onLogout={clearAuth} />;
}

function LoginPage({ onAuthed }: { onAuthed: (token: string, user: User) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [error, setError] = useState<string | null>(null);

  const submit = async (values: {
    username: string;
    password: string;
    employee_id?: string;
    real_name?: string;
  }) => {
    setError(null);
    try {
      if (mode === "register") {
        await register({
          username: values.username,
          password: values.password,
          employee_id: values.employee_id || "",
          real_name: values.real_name || ""
        });
      }
      const data = await login({ username: values.username, password: values.password });
      onAuthed(data.access_token, data.user);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "请求失败");
    }
  };

  return (
    <main className="loginPage">
      <section className="loginPanel">
        <Typography.Title level={2}>OpenIM</Typography.Title>
        <Segmented
          block
          value={mode}
          onChange={(value) => {
            setError(null);
            setMode(value as "login" | "register");
          }}
          options={[
            { label: "登录", value: "login" },
            { label: "注册", value: "register" }
          ]}
        />
        {error && <Alert type="error" message={error} showIcon />}
        <Form layout="vertical" onFinish={submit}>
          <Form.Item name="username" label="账号" rules={[{ required: true }]}>
            <Input autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}>
            <Input.Password autoComplete={mode === "login" ? "current-password" : "new-password"} />
          </Form.Item>
          {mode === "register" && (
            <>
              <Form.Item name="employee_id" label="工号" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="real_name" label="姓名" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
            </>
          )}
          <Button type="primary" htmlType="submit" block>
            {mode === "login" ? "登录" : "注册并登录"}
          </Button>
        </Form>
      </section>
    </main>
  );
}

function ChatPage({
  token,
  username,
  onLogout
}: {
  token: string;
  username: string;
  onLogout: () => void;
}) {
  const queryClient = useQueryClient();
  const [menu, setMenu] = useState<MenuKey>("sessions");
  const [selected, setSelected] = useState<SelectedView>({ type: "guide" });
  const [inputValue, setInputValue] = useState("");
  const [optimistic, setOptimistic] = useState<Record<string, ConversationMessage[]>>({});

  const contactsQuery = useQuery({ queryKey: ["contacts"], queryFn: () => contacts(token) });
  const conversationsQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: () => conversations(token)
  });

  useEmployeeWebSocket(token, queryClient);

  const selectedView = useMemo(
    () => resolveSelectedView(selected, contactsQuery.data?.all ?? []),
    [contactsQuery.data?.all, selected]
  );

  const activeConversation = useMemo(
    () =>
      selectedView.type === "conversation"
        ? conversationsQuery.data?.items.find((item) => item.id === selectedView.conversationId)
        : undefined,
    [conversationsQuery.data?.items, selectedView]
  );
  const messagesQuery = useQuery({
    queryKey: ["messages", activeConversation?.id],
    queryFn: () => conversationMessages(token, activeConversation!.id),
    enabled: Boolean(activeConversation?.id)
  });

  const ensureMutation = useMutation({
    mutationFn: (target: ProfileTarget) =>
      ensureConversation(token, targetTypeOf(target), targetIdOf(target)),
    onSuccess: (data) => {
      upsertConversationCache(queryClient, data.conversation);
      if (data.initial_messages.length) {
        queryClient.setQueryData<MessagePage>(["messages", data.conversation.id], {
          items: data.initial_messages,
          has_more: false,
          next_before: null
        });
      }
      setMenu("sessions");
      setSelected({ type: "conversation", conversationId: data.conversation.id });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err) => {
      message.error(err instanceof ApiError ? err.message : "打开会话失败");
    }
  });

  const addFriendMutation = useMutation({
    mutationFn: async (userId: number) => ({ userId, result: await addFriend(token, userId) }),
    onSuccess: ({ userId, result }) => {
      message.success("好友申请已发送");
      queryClient.setQueryData<{ items: User[] }>(["users"], (current) => ({
        items: (current?.items ?? []).map((item) =>
          item.id === userId ? { ...item, relationship: result.relationship } : item
        )
      }));
      queryClient.setQueryData<{ ai: ContactItem[]; all: ContactItem[] }>(["contacts"], (current) =>
        current ? updateContactUserRelationship(current, userId, result.relationship) : current
      );
      setSelected((current) =>
        current.type === "profile" && current.target.type === "user" && current.target.user.id === userId
          ? {
              type: "profile",
              target: {
                type: "user",
                user: { ...current.target.user, relationship: result.relationship }
              }
            }
          : current
      );
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
    },
    onError: (err) => {
      message.error(err instanceof ApiError ? err.message : "好友申请失败");
    }
  });

  const sendMutation = useMutation({
    mutationFn: (vars: { conversationId: string; content: string; tempId: string }) =>
      sendConversationMessage(token, vars.conversationId, vars.content),
    onSuccess: (data, vars) => {
      setOptimistic((current) => removeOptimistic(current, vars.conversationId, vars.tempId));
      mergeMessageCache(queryClient, vars.conversationId, data.messages);
      upsertConversationCache(queryClient, data.conversation);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err, vars) => {
      setOptimistic((current) => removeOptimistic(current, vars.conversationId, vars.tempId));
      message.error(err instanceof ApiError ? err.message : "消息发送失败");
    }
  });

  const visibleMessages = [
    ...(messagesQuery.data?.items ?? []),
    ...(activeConversation ? optimistic[activeConversation.id] ?? [] : [])
  ];

  const submitMessage = (value: string) => {
    if (!activeConversation) return;
    const content = value.trim();
    if (!content) return;
    const tempId = `temp_${Date.now()}`;
    setInputValue("");
    setOptimistic((current) => ({
      ...current,
      [activeConversation.id]: [
        ...(current[activeConversation.id] ?? []),
        {
          id: tempId,
          conversation_id: activeConversation.id,
          sender_type: "user",
          sender_id: "me",
          content_type: "text",
          content,
          status: "sending",
          created_at: new Date().toISOString(),
          client_message_id: tempId
        }
      ]
    }));
    sendMutation.mutate({ conversationId: activeConversation.id, content, tempId });
  };

  return (
    <main className="shell">
      <aside className="mainMenu">
        <div className="brand">OpenIM</div>
        <Button
          type={menu === "sessions" ? "primary" : "text"}
          icon={<UsersRound size={16} />}
          onClick={() => {
            setMenu("sessions");
            setSelected((current) => (current.type === "conversation" ? current : { type: "guide" }));
          }}
        >
          会话
        </Button>
        <Button
          type={menu === "contacts" ? "primary" : "text"}
          icon={<UsersRound size={16} />}
          onClick={() => {
            setMenu("contacts");
            setSelected({ type: "guide" });
          }}
        >
          通讯录
        </Button>
        <div className="menuSpacer" />
        <div className="accountFooter">
          <div className="accountName">{username}</div>
          <Button size="small" icon={<LogOut size={14} />} onClick={onLogout}>
            退出
          </Button>
        </div>
      </aside>

      <aside className="contacts">
        {menu === "sessions" ? (
          <SessionsList
            items={conversationsQuery.data?.items ?? []}
            selected={selectedView}
            onSelect={(conversationId) => setSelected({ type: "conversation", conversationId })}
          />
        ) : (
          <ContactsPanel
            ai={contactsQuery.data?.ai ?? []}
            all={contactsQuery.data?.all ?? []}
            selected={selectedView}
            onSelect={(target) => setSelected({ type: "profile", target })}
          />
        )}
      </aside>

      <section className="chat">
        {selectedView.type === "conversation" && activeConversation ? (
          <ConversationChat
            conversation={activeConversation}
            messages={visibleMessages}
            value={inputValue}
            loading={sendMutation.isPending}
            disabled={activeConversation.target_type === "openclaw_bot" && !activeConversation.online}
            disabledReason="OpenClaw 员工助手未连接，请先完成接入"
            onValueChange={setInputValue}
            onSubmit={submitMessage}
          />
        ) : selectedView.type === "profile" ? (
          <TargetProfile
            target={selectedView.target}
            adding={addFriendMutation.isPending}
            opening={ensureMutation.isPending}
            onAddFriend={(userId) => addFriendMutation.mutate(userId)}
            onOpenSession={() => ensureMutation.mutate(selectedView.target)}
          />
        ) : (
          <GuidePanel
            menu={menu}
            onOpenDefaultBot={() => ensureMutation.mutate({ type: "system_default_bot", id: "default_bot" })}
            opening={ensureMutation.isPending}
          />
        )}
      </section>
    </main>
  );
}

function SessionsList({
  items,
  selected,
  onSelect
}: {
  items: Conversation[];
  selected: SelectedView;
  onSelect: (conversationId: string) => void;
}) {
  if (!items.length) {
    return <div className="emptyList">暂无会话</div>;
  }
  return (
    <>
      <Typography.Text type="secondary">会话</Typography.Text>
      <List
        size="small"
        dataSource={items}
        renderItem={(item) => (
          <List.Item
            className={`contactItem ${
              selected.type === "conversation" && selected.conversationId === item.id ? "selected" : ""
            }`}
            onClick={() => onSelect(item.id)}
          >
            <ContactLine
              icon={item.target_type === "user" ? "user" : "bot"}
              title={item.title}
              subtitle={item.last_message || item.target_id}
              online={item.online}
            />
          </List.Item>
        )}
      />
    </>
  );
}

function ContactsPanel({
  ai,
  all,
  selected,
  onSelect
}: {
  ai: ContactItem[];
  all: ContactItem[];
  selected: SelectedView;
  onSelect: (target: ProfileTarget) => void;
}) {
  const activeProfile = selected.type === "profile" ? selected.target : undefined;
  return (
    <>
      <Typography.Text type="secondary">已添加的 AI</Typography.Text>
      <List
        size="small"
        dataSource={ai}
        renderItem={(item) => (
          <List.Item
            className={`contactItem ${isContactSelected(item, activeProfile) ? "selected" : ""}`}
            onClick={() => onSelect(profileTargetFromContact(item))}
          >
            <ContactLine
              icon="bot"
              title={item.title}
              subtitle={item.subtitle}
              online={item.online}
            />
          </List.Item>
        )}
      />

      <Typography.Text type="secondary">全部联系人</Typography.Text>
      <List
        size="small"
        dataSource={all}
        renderItem={(item) => (
          <List.Item
            className={`contactItem ${isContactSelected(item, activeProfile) ? "selected" : ""}`}
            onClick={() => onSelect(profileTargetFromContact(item))}
          >
            <ContactLine
              icon={item.contact_type === "user" ? "user" : "bot"}
              title={item.title}
              subtitle={contactSubtitle(item)}
              online={item.online}
            />
          </List.Item>
        )}
      />
    </>
  );
}

function ContactLine({
  icon,
  title,
  subtitle,
  online
}: {
  icon: "bot" | "user";
  title: string;
  subtitle: string;
  online: boolean;
}) {
  return (
    <div className="contactLine">
      <div className="contactIcon">{icon === "bot" ? <Bot size={16} /> : <UserRound size={16} />}</div>
      <div className="contactText">
        <div className="contactTitle">
          {online && <span className="onlineDot" />}
          <span>{title}</span>
        </div>
        <Typography.Text type="secondary" className="contactSubtitle">
          {subtitle}
        </Typography.Text>
      </div>
    </div>
  );
}

function TargetProfile({
  target,
  adding,
  opening,
  onAddFriend,
  onOpenSession
}: {
  target: ProfileTarget;
  adding: boolean;
  opening: boolean;
  onAddFriend: (userId: number) => void;
  onOpenSession: () => void;
}) {
  if (target.type === "system_default_bot") {
    return (
      <ProfileShell title="默认 BOT" subtitle="系统助手">
        <ProfileRow label="状态" value="在线" />
        <ProfileRow label="类型" value="系统默认助手" />
        <Button type="primary" loading={opening} onClick={onOpenSession}>
          发送消息
        </Button>
      </ProfileShell>
    );
  }
  if (target.type === "openclaw_bot") {
    const canMessage = target.bot.connect_status === "connected" && target.bot.binding_status === "active";
    return (
      <ProfileShell title={target.bot.name} subtitle={target.bot.bot_id}>
        <ProfileRow label="类型" value="公司 OpenClaw 员工助手" />
        <ProfileRow label="状态" value={target.bot.connect_status === "connected" ? "在线" : "离线"} />
        <ProfileRow label="绑定" value={target.bot.binding_status === "active" ? "已绑定" : "未绑定"} />
        {!canMessage && <Typography.Text type="secondary">请先通过默认 BOT 获取连接信息并启动 OpenClaw 接入。</Typography.Text>}
        <Button type="primary" loading={opening} disabled={!canMessage} onClick={onOpenSession}>
          发送消息
        </Button>
      </ProfileShell>
    );
  }

  const canMessage = target.user.relationship === "friend";
  return (
    <ProfileShell title={target.user.real_name} subtitle={`${target.user.username} · ${target.user.employee_id}`}>
      <ProfileRow label="状态" value={target.user.online ? "在线" : `离线，${leaveText(target.user.last_seen_at)}`} />
      <ProfileRow label="关系" value={relationshipText(target.user.relationship)} />
      {target.user.relationship === "none" && (
        <Button type="primary" loading={adding} onClick={() => onAddFriend(target.user.id)}>
          添加好友
        </Button>
      )}
      {target.user.relationship === "self" && <Typography.Text type="secondary">这是你自己</Typography.Text>}
      {target.user.relationship === "pending_out" && <Typography.Text type="secondary">等待对方确认</Typography.Text>}
      {target.user.relationship === "pending_in" && <Typography.Text type="secondary">对方已申请添加你</Typography.Text>}
      {canMessage && (
        <Button type="primary" loading={opening} onClick={onOpenSession}>
          发送消息
        </Button>
      )}
    </ProfileShell>
  );
}

function ConversationChat({
  conversation,
  messages,
  value,
  loading,
  disabled,
  disabledReason,
  onValueChange,
  onSubmit
}: {
  conversation: Conversation;
  messages: ConversationMessage[];
  value: string;
  loading: boolean;
  disabled?: boolean;
  disabledReason?: string;
  onValueChange: (value: string) => void;
  onSubmit: (value: string) => void;
}) {
  const quickCommands =
    conversation.target_type === "system_default_bot" ? ["/help", "/new-bot", "/my-bots"] : [];
  return (
    <>
      <header className="chatHeader">
        <div>
          <Typography.Title level={4}>{conversation.title}</Typography.Title>
          <Typography.Text type="secondary">{conversation.target_id}</Typography.Text>
        </div>
      </header>
      <div className="messageList">
        {messages.map((item) => (
          <div className={`message ${item.sender_type === "user" ? "user" : "bot"}`} key={item.id}>
            {item.content_type === "code" ? (
              <CopyableCodeBlock content={item.content} />
            ) : (
              <div className="bubble">{item.content}</div>
            )}
          </div>
        ))}
      </div>
      {disabled && disabledReason && <div className="chatNotice">{disabledReason}</div>}
      {quickCommands.length > 0 && (
        <div className="quickCommands">
          {quickCommands.map((command) => (
            <Button key={command} size="small" onClick={() => onSubmit(command)} disabled={loading}>
              {command}
            </Button>
          ))}
        </div>
      )}
      <form
        className="commandBar"
        onSubmit={(event) => {
          event.preventDefault();
          if (disabled || !value.trim()) return;
          onSubmit(value);
        }}
      >
        <Input
          value={value}
          onChange={(event) => onValueChange(event.target.value)}
          disabled={disabled}
          placeholder={`给 ${conversation.title} 发送消息`}
        />
        <Button
          aria-label="发送消息"
          htmlType="submit"
          type="primary"
          icon={<Send size={16} />}
          loading={loading}
          disabled={disabled || !value.trim()}
        />
      </form>
    </>
  );
}

function ProfileShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="profilePanel">
      <Typography.Title level={3}>{title}</Typography.Title>
      <Typography.Text type="secondary">{subtitle}</Typography.Text>
      <div className="profileDetails">{children}</div>
    </div>
  );
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="profileRow">
      <Typography.Text type="secondary">{label}</Typography.Text>
      <Typography.Text>{value}</Typography.Text>
    </div>
  );
}

function GuidePanel({
  menu,
  opening,
  onOpenDefaultBot
}: {
  menu: MenuKey;
  opening: boolean;
  onOpenDefaultBot: () => void;
}) {
  return (
    <div className="guidePanel">
      <Typography.Title level={3}>
        {menu === "sessions" ? "开始接入 OpenClaw 员工助手" : "选择联系人或 AI"}
      </Typography.Title>
      <Typography.Text type="secondary">
        {menu === "sessions" ? "通过默认 BOT 创建接入槽位并获取连接信息。" : "从左侧选择一个对象，查看资料并开始操作。"}
      </Typography.Text>
      {menu === "sessions" && (
        <div className="guideActions">
          <Button type="primary" loading={opening} onClick={onOpenDefaultBot}>
            打开默认 BOT
          </Button>
        </div>
      )}
    </div>
  );
}

function useEmployeeWebSocket(token: string, queryClient: ReturnType<typeof useQueryClient>) {
  useEffect(() => {
    const url = employeeWsUrl(token);
    const socket = new WebSocket(url);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as {
        type: string;
        message?: ConversationMessage;
        conversation?: Conversation;
      };
      if (payload.type === "message.new" && payload.message) {
        mergeMessageCache(queryClient, payload.message.conversation_id, [payload.message]);
      }
      if (payload.type === "conversation.updated" && payload.conversation) {
        upsertConversationCache(queryClient, payload.conversation);
      }
    };
    return () => socket.close();
  }, [queryClient, token]);
}

function employeeWsUrl(token: string) {
  const apiBase = import.meta.env.VITE_API_BASE_URL || "/api";
  const base = apiBase.startsWith("http") ? new URL(apiBase) : new URL(apiBase, window.location.origin);
  const url = new URL("/ws", base.origin);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("token", token);
  return url.toString();
}

function targetTypeOf(target: ProfileTarget) {
  return target.type;
}

function targetIdOf(target: ProfileTarget) {
  if (target.type === "system_default_bot") return target.id;
  if (target.type === "openclaw_bot") return target.bot.bot_id;
  return String(target.user.id);
}

function resolveSelectedView(selected: SelectedView, contacts: ContactItem[]): SelectedView {
  if (selected.type !== "profile") return selected;
  const target = selected.target;
  if (target.type === "user") {
    const contact = contacts.find((item) => item.contact_type === "user" && item.user.id === target.user.id);
    return contact && contact.contact_type === "user"
      ? { type: "profile", target: { type: "user", user: contact.user } }
      : selected;
  }
  if (target.type === "openclaw_bot") {
    const contact = contacts.find(
      (item) => item.contact_type === "openclaw_bot" && item.bot.bot_id === target.bot.bot_id
    );
    return contact && contact.contact_type === "openclaw_bot"
      ? { type: "profile", target: { type: "openclaw_bot", bot: contact.bot } }
      : selected;
  }
  return selected;
}

function upsertConversationCache(queryClient: ReturnType<typeof useQueryClient>, conversation: Conversation) {
  queryClient.setQueryData<{ items: Conversation[] }>(["conversations"], (current) => ({
    items: [conversation, ...(current?.items ?? []).filter((item) => item.id !== conversation.id)]
  }));
}

function mergeMessageCache(
  queryClient: ReturnType<typeof useQueryClient>,
  conversationId: string,
  messages: ConversationMessage[]
) {
  queryClient.setQueryData<MessagePage>(["messages", conversationId], (current) => {
    const existing = current?.items ?? [];
    const next = [...existing];
    for (const messageItem of messages) {
      if (!next.some((item) => item.id === messageItem.id)) {
        next.push(messageItem);
      }
    }
    return { items: next, has_more: current?.has_more ?? false, next_before: current?.next_before ?? null };
  });
}

function removeOptimistic(
  current: Record<string, ConversationMessage[]>,
  conversationId: string,
  tempId: string
) {
  return {
    ...current,
    [conversationId]: (current[conversationId] ?? []).filter((item) => item.id !== tempId)
  };
}

function profileTargetFromContact(item: ContactItem): ProfileTarget {
  if (item.contact_type === "system_default_bot") return { type: "system_default_bot", id: "default_bot" };
  if (item.contact_type === "openclaw_bot") return { type: "openclaw_bot", bot: item.bot };
  return { type: "user", user: item.user };
}

function isContactSelected(item: ContactItem, selected?: ProfileTarget) {
  if (!selected) return false;
  if (item.contact_type === "system_default_bot") return selected.type === "system_default_bot";
  if (item.contact_type === "openclaw_bot") {
    return selected.type === "openclaw_bot" && selected.bot.bot_id === item.bot.bot_id;
  }
  return selected.type === "user" && selected.user.id === item.user.id;
}

function contactSubtitle(item: ContactItem) {
  if (item.contact_type !== "user") return item.subtitle;
  if (item.online) return item.user.username;
  return leaveText(item.user.last_seen_at);
}

function updateContactUserRelationship(
  current: { ai: ContactItem[]; all: ContactItem[] },
  userId: number,
  relationship: User["relationship"]
) {
  return {
    ...current,
    all: current.all.map((item) =>
      item.contact_type === "user" && item.user.id === userId
        ? { ...item, user: { ...item.user, relationship } }
        : item
    )
  };
}

function relationshipText(value: User["relationship"]) {
  if (value === "self") return "这是你自己";
  if (value === "friend") return "已添加";
  if (value === "pending_out") return "等待对方确认";
  if (value === "pending_in") return "对方申请中";
  return "未添加";
}

function leaveText(value: string | null) {
  if (!value) return "离线";
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "刚刚离开";
  if (minutes < 60) return `${minutes} 分钟前离开`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小时前离开`;
  const days = Math.floor(hours / 24);
  return `${days} 天前离开`;
}
