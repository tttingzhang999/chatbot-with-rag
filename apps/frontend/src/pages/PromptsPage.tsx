import { useEffect, useState } from 'react';
import { Plus, RefreshCw, Trash2, Edit, Star } from 'lucide-react';
import { useProfileStore } from '@/stores/profileStore';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { ProfileDialog } from '@/components/profiles/ProfileDialog';
import type { PromptProfile } from '@/types/profile';
import { toast } from 'sonner';

export function PromptsPage() {
  const {
    profiles,
    currentProfile,
    fetchProfiles,
    deleteProfile,
    setDefaultProfile,
    isLoading,
  } = useProfileStore();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState<PromptProfile | null>(null);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleCreateNew = () => {
    setEditingProfile(null);
    setDialogOpen(true);
  };

  const handleEdit = async (profileId: string) => {
    try {
      // Fetch full profile details
      const { setCurrentProfile } = useProfileStore.getState();
      await setCurrentProfile(profileId);
      const profile = useProfileStore.getState().currentProfile;
      if (profile) {
        setEditingProfile(profile);
        setDialogOpen(true);
      }
    } catch (error) {
      toast.error('Failed to load profile details');
    }
  };

  const handleDelete = async (profileId: string, profileName: string) => {
    if (!confirm(`Are you sure you want to delete profile "${profileName}"? This will also delete all associated conversations and documents.`)) {
      return;
    }

    try {
      await deleteProfile(profileId);
      toast.success('Profile deleted successfully');
    } catch (error: any) {
      toast.error(error.message || 'Failed to delete profile');
    }
  };

  const handleSetDefault = async (profileId: string, profileName: string) => {
    try {
      await setDefaultProfile(profileId);
      toast.success(`"${profileName}" is now your default profile`);
    } catch (error: any) {
      toast.error(error.message || 'Failed to set default profile');
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="shrink-0 px-6 py-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h1 className="text-2xl font-bold tracking-tight">Prompt Profiles</h1>
            <p className="text-sm text-muted-foreground">
              Manage your RAG chatbot configurations with custom prompts and settings
            </p>
          </div>
          <Button onClick={handleCreateNew}>
            <Plus className="h-4 w-4 mr-2" />
            Create Profile
          </Button>
        </div>
        <Separator />
      </div>

      <div className="flex-1 min-h-0 px-6 pb-6">
        <Card className="h-full flex flex-col">
          <CardHeader className="shrink-0 pb-3">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>Your Profiles</CardTitle>
                <CardDescription>
                  Each profile has independent conversations, documents, prompts, and LLM settings
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchProfiles()}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent className="flex-1 min-h-0 p-0">
            <ScrollArea className="h-full px-6">
              <div className="space-y-3 pb-6">
                {profiles.length === 0 && !isLoading && (
                  <div className="text-center py-12 text-muted-foreground">
                    <p>No profiles found. Create your first profile to get started!</p>
                  </div>
                )}
                {profiles.map((profile) => (
                  <Card
                    key={profile.id}
                    className={`transition-all ${
                      currentProfile?.id === profile.id ? 'ring-2 ring-primary' : ''
                    }`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{profile.name}</h3>
                            {profile.is_default && (
                              <Badge variant="secondary">
                                <Star className="h-3 w-3 mr-1" />
                                Default
                              </Badge>
                            )}
                            {currentProfile?.id === profile.id && (
                              <Badge variant="outline">Current</Badge>
                            )}
                          </div>
                          {profile.description && (
                            <p className="text-sm text-muted-foreground">
                              {profile.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
                            <span>Created: {new Date(profile.created_at).toLocaleDateString()}</span>
                            <span>Updated: {new Date(profile.updated_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 ml-4">
                          {!profile.is_default && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleSetDefault(profile.id, profile.name)}
                              title="Set as default"
                            >
                              <Star className="h-4 w-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(profile.id)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          {!profile.is_default && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDelete(profile.id, profile.name)}
                              className="text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      <ProfileDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        profile={editingProfile}
        onSuccess={() => {
          setDialogOpen(false);
          setEditingProfile(null);
          fetchProfiles();
        }}
      />
    </div>
  );
}
