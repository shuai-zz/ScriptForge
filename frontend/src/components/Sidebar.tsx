import { NavLink, useParams } from "react-router-dom";
import {
  BookOpen,
  Clapperboard,
  FileText,
  Home,
  LayoutDashboard,
  ScrollText,
  Settings,
  Users,
} from "lucide-react";

export default function Sidebar() {
  const { projectId } = useParams<{ projectId?: string }>();

  return (
    <aside className="flex w-16 flex-col items-center border-r border-border bg-surface py-4">
      {/* Logo */}
      <div className="mb-6 flex h-10 w-10 items-center justify-center rounded-lg bg-primary-muted">
        <Clapperboard className="h-5 w-5 text-primary" />
      </div>

      {/* Global Nav */}
      <nav className="flex flex-col gap-1">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
              isActive
                ? "bg-primary-muted text-primary"
                : "text-text-secondary hover:bg-card hover:text-text-primary"
            }`
          }
          title="项目"
        >
          <Home className="h-5 w-5" />
        </NavLink>
      </nav>

      {/* Project Nav */}
      {projectId && (
        <nav className="mt-4 flex flex-col gap-1 border-t border-border pt-4">
          <SidebarLink to={`/projects/${projectId}`} icon={BookOpen} label="章节" />
          <SidebarLink to={`/projects/${projectId}/script`} icon={ScrollText} label="剧本" />
          <SidebarLink to={`/projects/${projectId}/characters`} icon={Users} label="角色" />
          <SidebarLink to={`/projects/${projectId}/story-bible`} icon={FileText} label="圣经" />
          <SidebarLink to={`/projects/${projectId}/stats`} icon={LayoutDashboard} label="统计" />
          <SidebarLink to={`/projects/${projectId}/versions`} icon={Settings} label="版本" />
        </nav>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Version */}
      <span className="text-xs text-text-muted">v0.1</span>
    </aside>
  );
}

function SidebarLink({
  to,
  icon: Icon,
  label,
}: {
  to: string;
  icon: React.FC<{ className?: string }>;
  label: string;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex h-10 w-10 items-center justify-center rounded-lg transition-colors ${
          isActive
            ? "bg-primary-muted text-primary"
            : "text-text-secondary hover:bg-card hover:text-text-primary"
        }`
      }
      title={label}
    >
      <Icon className="h-5 w-5" />
    </NavLink>
  );
}
