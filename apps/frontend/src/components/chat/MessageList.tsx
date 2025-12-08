import { useEffect, useRef } from 'react';
import { Message } from './Message';
import { TypingIndicator } from './TypingIndicator';
import type { Message as MessageType } from '@/types/chat';
import { ScrollArea } from '@/components/ui/scroll-area';

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
}

export const MessageList = ({ messages, isLoading }: MessageListProps) => {
  const viewportRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end'
    });
  }, [messages, isLoading]);

  return (
    <ScrollArea className="h-full w-full px-4" viewportRef={viewportRef}>
      <div className="space-y-4 py-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex items-center justify-center min-h-[400px] text-muted-foreground">
            <div className="text-center space-y-4 max-w-md px-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-2xl">💬</span>
              </div>
              <div className="space-y-2">
                <p className="text-lg font-semibold text-foreground">Welcome to HR Chatbot</p>
                <p className="text-sm">Ask me anything about HR policies, benefits, or company information. I'm here to help!</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center pt-4">
                <div className="px-3 py-2 bg-muted rounded-lg text-xs">
                  What are the vacation policies?
                </div>
                <div className="px-3 py-2 bg-muted rounded-lg text-xs">
                  How do I submit expenses?
                </div>
                <div className="px-3 py-2 bg-muted rounded-lg text-xs">
                  What are the benefits?
                </div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}

        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>
    </ScrollArea>
  );
};
