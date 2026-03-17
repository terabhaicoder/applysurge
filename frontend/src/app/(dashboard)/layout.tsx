'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/layout/sidebar';
import { Navbar } from '@/components/layout/navbar';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUIStore();
  const pathname = usePathname();

  // Setup wizard gets a clean full-page layout (no sidebar/navbar)
  if (pathname === '/setup') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className={cn('transition-all duration-300', sidebarOpen ? 'lg:ml-60' : 'lg:ml-[70px]')}>
        <Navbar />
        <main className="p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
