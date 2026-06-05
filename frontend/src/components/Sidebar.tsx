import { NavLink } from "react-router-dom";
import { Clapperboard, Home, Settings } from "lucide-react";

const navItems = [
  { to: "/", icon: Home, label: "项目" },
  { to: "/settings", icon: Settings, label: "设置" },
];

export default function Sidebar() {
  return (
    <aside className="flex w-16 flex-col items-center border-r border-border bg-surface py-4">
      {/* Logo */}
      <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-muted">
        <Clapperboard className="h-5 w-5 text-primary" />
      </div>

      {/* Nav Items */}
      <nav className="flex flex-col gap-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
                isActive
                  ? "bg-primary-muted text-primary"
                  : "text-text-secondary hover:bg-card hover:text-text-primary"
              }`
            }
            title={item.label}
          >
            <item.icon className="h-5 w-5" />
          </NavLink>
        ))}
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Version */}
      <span className="text-xs text-text-muted">v0.1</span>
    </aside>
  );
}
