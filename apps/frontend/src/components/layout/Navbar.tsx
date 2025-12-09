import { useAuthStore } from '@/stores/authStore';
import { useProfileStore } from '@/stores/profileStore';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { LogOut, MessageSquare, FileText, Settings, Check } from 'lucide-react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useEffect } from 'react';
import { cn } from '@/lib/utils';
import { ThemeToggle } from '@/components/theme/ThemeToggle';
import { toast } from 'sonner';

export const Navbar = () => {
  const { user, logout } = useAuthStore();
  const {
    profiles,
    currentProfile,
    fetchProfiles,
    fetchDefaultProfile,
    setCurrentProfile,
  } = useProfileStore();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetchProfiles();
    if (!currentProfile) {
      fetchDefaultProfile();
    }
  }, [fetchProfiles, fetchDefaultProfile, currentProfile]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleProfileChange = async (profileId: string) => {
    try {
      await setCurrentProfile(profileId);
      toast.success('Profile switched successfully');
    } catch (error: any) {
      toast.error(error.message || 'Failed to switch profile');
    }
  };

  const navItems = [
    { path: '/', label: 'Chat', icon: MessageSquare },
    { path: '/documents', label: 'Documents', icon: FileText },
    { path: '/prompts', label: 'Prompts', icon: Settings },
  ];

  return (
    <nav className="border-b bg-background">
      <div className="flex h-16 items-center px-4 justify-between">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold">RAG Chatbot</h1>

          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link key={item.path} to={item.path}>
                  <Button
                    variant={isActive ? 'secondary' : 'ghost'}
                    className={cn(
                      'gap-2',
                      isActive && 'bg-secondary'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                  </Button>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Profile Selector */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="gap-2">
                <Settings className="h-4 w-4" />
                <span className="hidden sm:inline">
                  {currentProfile?.name || 'Select Profile'}
                </span>
                {currentProfile?.is_default && (
                  <Badge variant="secondary" className="ml-1 hidden lg:inline-flex">
                    Default
                  </Badge>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="end">
              <DropdownMenuLabel>Switch Profile</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {profiles.map((profile) => (
                <DropdownMenuItem
                  key={profile.id}
                  onClick={() => handleProfileChange(profile.id)}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex flex-col">
                    <span className="font-medium">{profile.name}</span>
                    {profile.description && (
                      <span className="text-xs text-muted-foreground line-clamp-1">
                        {profile.description}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1">
                    {profile.is_default && (
                      <Badge variant="secondary" className="text-xs">
                        Default
                      </Badge>
                    )}
                    {currentProfile?.id === profile.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </div>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/prompts')}>
                <Settings className="mr-2 h-4 w-4" />
                <span>Manage Profiles</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <ThemeToggle />

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {user?.username?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user?.username}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  );
};
