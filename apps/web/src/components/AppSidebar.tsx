import { Button } from "antd";
import { LogOut, MessageCircle, UsersRound } from "lucide-react";

type MenuKey = "sessions" | "contacts";

export function AppSidebar({
  menu,
  username,
  onMenuChange,
  onLogout
}: {
  menu: MenuKey;
  username: string;
  onMenuChange: (menu: MenuKey) => void;
  onLogout: () => void;
}) {
  return (
    <aside className="appSidebar" aria-label="OpenIM 主导航">
      <div className="sidebarBrand">OpenIM</div>
      <nav className="sidebarNav" aria-label="主导航">
        <button
          type="button"
          className={`sidebarNavItem ${menu === "sessions" ? "active" : ""}`}
          aria-current={menu === "sessions" ? "page" : undefined}
          onClick={() => onMenuChange("sessions")}
        >
          <MessageCircle size={18} />
          <span>会话</span>
        </button>
        <button
          type="button"
          className={`sidebarNavItem ${menu === "contacts" ? "active" : ""}`}
          aria-current={menu === "contacts" ? "page" : undefined}
          onClick={() => onMenuChange("contacts")}
        >
          <UsersRound size={18} />
          <span>通讯录</span>
        </button>
      </nav>
      <div className="sidebarSpacer" />
      <div className="sidebarAccount">
        <div className="sidebarAccountName" title={username}>
          {username}
        </div>
        <Button aria-label="退出登录" size="small" icon={<LogOut size={14} />} onClick={onLogout}>
          退出
        </Button>
      </div>
    </aside>
  );
}
