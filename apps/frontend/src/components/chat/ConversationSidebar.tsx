import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import type { Conversation } from '@/types/chat';
import { MessageSquarePlus, MessageSquare, Trash2, RefreshCw } from 'lucide-react';

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (conversationId: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  isLoading?: boolean;
}

export const ConversationSidebar = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRefresh,
  isRefreshing = false,
  isLoading = false,
}: ConversationSidebarProps) => {
  return (
    <div className="w-64 border-r bg-muted/10 flex flex-col h-full">
      <div className="p-4 space-y-2">
        <Button onClick={onNewConversation} className="w-full" variant="default">
          <MessageSquarePlus className="h-4 w-4 mr-2" />
          New Chat
        </Button>
        <Button
          onClick={onRefresh}
          className="w-full"
          variant="outline"
          disabled={isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Separator />

      <ScrollArea className="flex-1">
        <div className="p-2 space-y-1">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg p-3">
                <Skeleton className="h-4 w-4 shrink-0" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-3 w-20" />
                </div>
              </div>
            ))
          ) : conversations.length === 0 ? (
            <div className="text-center py-8 px-4">
              <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-muted flex items-center justify-center">
                <MessageSquare className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground mb-1">No conversations yet</p>
              <p className="text-xs text-muted-foreground">Click "New Chat" to start</p>
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`group relative flex items-center gap-2 rounded-lg p-3 hover:bg-muted/50 cursor-pointer transition-colors ${
                  activeConversationId === conversation.id ? 'bg-muted' : ''
                }`}
                onClick={() => onSelectConversation(conversation.id)}
              >
                <MessageSquare className="h-4 w-4 shrink-0" />
                <div className="flex-1 min-w-0 overflow-hidden">
                  <p className="text-sm font-medium truncate">
                    {conversation.title || 'Untitled'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(conversation.updated_at).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conversation.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
};
