export const TypingIndicator = () => {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
        <span className="text-sm font-medium">AI</span>
      </div>
      <div className="flex-1">
        <div className="inline-block bg-muted rounded-lg px-4 py-3">
          <div className="flex gap-1">
            <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce [animation-delay:-0.3s]" />
            <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce [animation-delay:-0.15s]" />
            <div className="w-2 h-2 rounded-full bg-foreground/40 animate-bounce" />
          </div>
        </div>
      </div>
    </div>
  );
};
