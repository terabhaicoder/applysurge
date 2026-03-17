'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  Briefcase,
  FileText,
  FileUp,
  SlidersHorizontal,
  Link2,
  BarChart3,
  Mail,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Settings,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/stores/ui-store';
import { useAuthStore } from '@/stores/auth-store';
import { clearTokens } from '@/lib/auth';
import { LogoAppIcon } from '@/components/ui/logo';
import { ThemeToggle } from '@/components/ui/theme-toggle';

/* ------------------------------------------------------------------ */
/*  Navigation structure                                               */
/* ------------------------------------------------------------------ */

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const sections: NavSection[] = [
  {
    title: 'MAIN',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { href: '/agent', label: 'Agent', icon: Bot },
      { href: '/jobs', label: 'Jobs', icon: Briefcase },
      { href: '/applications', label: 'Applications', icon: FileText },
    ],
  },
  {
    title: 'SETUP',
    items: [
      { href: '/resume', label: 'Resume', icon: FileUp },
      { href: '/preferences', label: 'Preferences', icon: SlidersHorizontal },
      { href: '/connections', label: 'Connections', icon: Link2 },
    ],
  },
  {
    title: 'MORE',
    items: [
      { href: '/analytics', label: 'Analytics', icon: BarChart3 },
      { href: '/emails', label: 'Emails', icon: Mail },
    ],
  },
];

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function getInitials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

/* ------------------------------------------------------------------ */
/*  Sidebar                                                            */
/* ------------------------------------------------------------------ */

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    clearTokens();
    logout();
    router.push('/login');
  };

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden transition-opacity duration-300',
          sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={toggleSidebar}
      />

      {/* Sidebar panel */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-screen flex-col bg-background border-r border-border/60 transition-all duration-300 ease-in-out',
          sidebarOpen
            ? 'w-60 translate-x-0'
            : 'w-[70px] -translate-x-full lg:translate-x-0'
        )}
      >
        {/* ── Header / Logo ── */}
        <div className={cn(
          'flex h-14 items-center border-b border-border/40 flex-shrink-0',
          sidebarOpen ? 'justify-between px-4' : 'flex-col justify-center gap-1 px-2 h-auto py-3'
        )}>
          <Link
            href="/dashboard"
            className="flex items-center gap-2.5"
          >
            <LogoAppIcon size={sidebarOpen ? 32 : 28} className="flex-shrink-0" />
            {sidebarOpen && (
              <span className="text-base font-display font-bold text-foreground tracking-tight whitespace-nowrap">
                Apply Surge
              </span>
            )}
          </Link>

          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-all duration-200"
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        </div>

        {/* ── Navigation sections ── */}
        <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-2.5 space-y-5">
          {sections.map((section) => (
            <div key={section.title}>
              {/* Section label */}
              {sidebarOpen && (
                <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted-foreground/70 select-none">
                  {section.title}
                </p>
              )}

              {/* Divider when collapsed (replaces text label) */}
              {!sidebarOpen && (
                <div className="mx-auto mb-2 h-px w-6 bg-border/50" />
              )}

              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    pathname.startsWith(item.href + '/');

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      title={!sidebarOpen ? item.label : undefined}
                      className={cn(
                        'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                        isActive
                          ? 'bg-primary/[0.08] text-primary font-semibold'
                          : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground'
                      )}
                    >
                      {/* Active accent bar */}
                      {isActive && (
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-primary" />
                      )}

                      <item.icon
                        className={cn(
                          'h-[18px] w-[18px] flex-shrink-0 transition-colors duration-200',
                          isActive
                            ? 'text-primary'
                            : 'text-muted-foreground/80 group-hover:text-foreground'
                        )}
                      />

                      {sidebarOpen && (
                        <span className="truncate">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* ── Bottom user section ── */}
        <div className="flex-shrink-0 border-t border-border/40 p-3">
          {sidebarOpen ? (
            <>
              {/* User info row */}
              <div className="flex items-center gap-3 rounded-lg px-2 py-2">
                {/* Avatar */}
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold ring-1 ring-primary/10">
                  {user?.full_name ? getInitials(user.full_name) : <User className="h-4 w-4" />}
                </div>

                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">
                    {user?.full_name || 'User'}
                  </p>
                  <p className="truncate text-xs text-muted-foreground/70">
                    {user?.email || ''}
                  </p>
                </div>
              </div>

              {/* Action row */}
              <div className="mt-1 flex items-center gap-1 px-2">
                <Link
                  href="/settings"
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium text-muted-foreground hover:bg-secondary/80 hover:text-foreground transition-all duration-200"
                >
                  <Settings className="h-3.5 w-3.5" />
                  <span>Settings</span>
                </Link>

                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200 ml-auto"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Log out</span>
                </button>
              </div>
            </>
          ) : (
            /* Collapsed: just avatar + icon buttons stacked */
            <div className="flex flex-col items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold ring-1 ring-primary/10">
                {user?.full_name ? getInitials(user.full_name) : <User className="h-4 w-4" />}
              </div>

              <Link
                href="/settings"
                title="Settings"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-secondary/80 hover:text-foreground transition-all duration-200"
              >
                <Settings className="h-4 w-4" />
              </Link>

              <button
                onClick={handleLogout}
                title="Log out"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-all duration-200"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
