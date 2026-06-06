import type { FC } from "react";
import { NavLink, useParams } from "react-router-dom";
import {
  BookOpen,
  Bot,
  Clapperboard,
  FileText,
  Home,
  LayoutDashboard,
  ScrollText,
  Settings,
  Users,
  X,
} from "lucide-react";

interface SidebarProps {
  onClose?: () => void;
}

export default function Sidebar({ onClose }: SidebarProps) {
  const { projectId } = useParams<{ projectId?: string }>();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-neutral-800 bg-neutral-900 py-4 md:w-16 md:items-center">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between px-4 md:px-0 md:justify-center">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-900/30">
          <Clapperboard className="h-5 w-5 text-amber-500" />
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200 md:hidden"
            aria-label="关闭菜单"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Global Nav */}
      <nav className="flex flex-col gap-1 px-2 md:px-0 md:items-center">
        <SidebarLink to="/" icon={Home} label="项目" onClick={onClose} />
      </nav>

      {/* Project Nav */}
      {projectId && (
        <nav className="mt-4 flex flex-col gap-1 border-t border-neutral-800 px-2 pt-4 md:px-0 md:items-center">
          <SidebarLink to={`/projects/${projectId}`} icon={BookOpen} label="章节" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/script`} icon={ScrollText} label="剧本" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/characters`} icon={Users} label="角色" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/story-bible`} icon={FileText} label="圣经" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/stats`} icon={LayoutDashboard} label="统计" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/versions`} icon={Settings} label="版本" onClick={onClose} />
          <SidebarLink to={`/projects/${projectId}/providers`} icon={Bot} label="模型" onClick={onClose} />
        </nav>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Version */}
      <span className="px-4 text-xs text-neutral-600 md:px-0">v0.1</span>
    </aside>
  );
}

function SidebarLink({
  to,
  icon: Icon,
  label,
  onClick,
}: {
  to: string;
  icon: FC<{ className?: string }>;
  label: string;
  onClick?: () => void;
}) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors md:h-10 md:w-10 md:justify-center md:p-0 ${
          isActive
            ? "bg-amber-900/30 text-amber-500"
            : "text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200"
        }`
      }
      title={label}
    >
      <Icon className="h-5 w-5 shrink-0" />
      <span className="text-sm md:hidden">{label}</span>
    </NavLink>
  );
}
