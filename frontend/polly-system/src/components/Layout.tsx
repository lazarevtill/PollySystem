import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  LayoutGrid,
  Server,
  Box,
  Activity,
  Settings as SettingsIcon,
  Menu,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { useMediaQuery } from '@/hooks/use-media-query';

const menuItems = [
  { path: '/', label: 'Dashboard', icon: LayoutGrid },
  { path: '/machines', label: 'Machines', icon: Server },
  { path: '/deployments', label: 'Deployments', icon: Box },
  { path: '/monitoring', label: 'Monitoring', icon: Activity },
  { path: '/settings', label: 'Settings', icon: SettingsIcon },
];

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const location = useLocation();
  const isMobile = useMediaQuery('(max-width: 768px)');

  const SidebarContent = () => (
    <div className="space-y-4 py-4">
      <div className="px-3 py-2">
        <h2 className="mb-2 px-4 text-lg font-semibold">Infrastructure Manager</h2>
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.path} to={item.path}>
                <Button
                  variant={location.pathname === item.path ? 'secondary' : 'ghost'}
                  className="w-full justify-start"
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {item.label}
                </Button>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen">
      {isMobile ? (
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden">
              <Menu className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64">
            <SheetHeader>
              <SheetTitle>Menu</SheetTitle>
            </SheetHeader>
            <SidebarContent />
          </SheetContent>
        </Sheet>
      ) : (
        <div className="hidden w-64 border-r bg-muted/40 md:block">
          <SidebarContent />
        </div>
      )}
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}

export default Layout;
