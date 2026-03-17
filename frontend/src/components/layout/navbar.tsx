'use client';

import { Bell, Search, Menu, Command } from 'lucide-react';
import { useUIStore } from '@/stores/ui-store';
import { useNotificationStore } from '@/stores/notification-store';
import { UserMenu } from './user-menu';
import { ThemeToggle } from '@/components/ui/theme-toggle';

export function Navbar() {
  const { toggleSidebar } = useUIStore();
  const { unreadCount } = useNotificationStore();

  return (
    <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-xl border-b border-border/40">
      <div className="flex items-center justify-between h-14 px-4 sm:px-6">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-all duration-200"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Search */}
          <div className="hidden sm:flex items-center gap-3 bg-background hover:bg-secondary/40 rounded-xl px-4 py-2 w-72 border border-border hover:border-border transition-all duration-200 cursor-pointer group">
            <Search className="w-4 h-4 text-muted-foreground/70" />
            <span className="text-sm text-muted-foreground/70 flex-1">Search jobs, applications...</span>
            <kbd className="hidden md:flex items-center gap-1 px-1.5 py-0.5 bg-secondary/60 rounded text-[10px] text-muted-foreground font-medium border border-border/50">
              <Command className="w-2.5 h-2.5" />K
            </kbd>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Notifications */}
          <button className="relative p-2.5 rounded-lg hover:bg-secondary/80 text-muted-foreground hover:text-foreground transition-all duration-200">
            <Bell className="w-[18px] h-[18px]" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 min-w-[16px] h-[16px] px-1 bg-primary text-primary-foreground text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Divider */}
          <div className="w-px h-6 bg-border/40 mx-1" />

          {/* User Menu */}
          <UserMenu />
        </div>
      </div>
    </header>
  );
}
