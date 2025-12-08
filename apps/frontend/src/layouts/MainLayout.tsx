import { Outlet } from 'react-router-dom';
import { Navbar } from '@/components/layout/Navbar';

export const MainLayout = () => {
  return (
    <div className="flex flex-col h-screen">
      <Navbar />
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
};
