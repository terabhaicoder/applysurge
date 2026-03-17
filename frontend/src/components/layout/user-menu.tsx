'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { User, Settings, LogOut, CreditCard, ChevronDown } from 'lucide-react';
import { useAuthStore } from '@/stores/auth-store';
import { useAuth } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';

export function UserMenu() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const { user } = useAuthStore();
  const { logout } = useAuth();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-secondary transition-colors"
      >
        <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
          <span className="text-sm font-semibold text-primary-foreground">
            {user?.full_name?.charAt(0) || 'U'}
          </span>
        </div>
        <span className="hidden sm:block text-sm font-medium text-foreground max-w-[100px] truncate">
          {user?.full_name || 'User'}
        </span>
        <ChevronDown className={cn('w-4 h-4 text-muted-foreground transition-transform hidden sm:block', open && 'rotate-180')} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-card rounded-xl shadow-lg border border-border py-1 z-50 animate-in fade-in-0 zoom-in-95">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-sm font-medium text-foreground">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>

          <div className="py-1">
            <Link
              href="/settings/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
            >
              <User className="w-4 h-4 text-muted-foreground" />
              Profile
            </Link>
            <Link
              href="/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
            >
              <Settings className="w-4 h-4 text-muted-foreground" />
              Settings
            </Link>
            <Link
              href="/settings/billing"
              onClick={() => setOpen(false)}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-secondary transition-colors"
            >
              <CreditCard className="w-4 h-4 text-muted-foreground" />
              Billing
            </Link>
          </div>

          <div className="border-t border-border py-1">
            <button
              onClick={() => { logout(); setOpen(false); }}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-destructive hover:bg-destructive/10 w-full transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
