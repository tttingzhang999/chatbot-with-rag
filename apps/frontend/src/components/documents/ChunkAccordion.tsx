import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { getDocumentChunks } from "@/services/embedService";

interface ChunkAccordionProps {
  documentId: string;
  documentName: string;
}

export function ChunkAccordion({ documentId }: ChunkAccordionProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['chunks', documentId],
    queryFn: () => getDocumentChunks(documentId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-destructive p-4">
        Failed to load chunks: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    );
  }

  const totalChars = data?.chunks.reduce((sum, chunk) => {
    const charCount = typeof chunk.metadata?.char_count === 'number' ? chunk.metadata.char_count : 0;
    return sum + charCount;
  }, 0) || 0;

  return (
    <div className="border rounded-lg p-4 space-y-4 bg-muted/30">
      {/* Document Summary */}
      <div className="flex items-center gap-6">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Total Chunks</p>
          <p className="text-2xl font-bold">{data?.total || 0}</p>
        </div>
        <div>
          <p className="text-sm font-medium text-muted-foreground">Total Characters</p>
          <p className="text-2xl font-bold">{totalChars.toLocaleString()}</p>
        </div>
      </div>

      {/* Individual Chunks */}
      {data && data.chunks.length > 0 ? (
        <Accordion type="single" collapsible className="w-full">
          {data.chunks.map((chunk) => (
            <AccordionItem key={chunk.id} value={`chunk-${chunk.id}`}>
              <AccordionTrigger>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">Chunk {chunk.chunk_index}</Badge>
                  <Badge variant="secondary">
                    {typeof chunk.metadata?.char_count === 'number' ? chunk.metadata.char_count : 0} chars
                  </Badge>
                  {chunk.embedding_dimension && (
                    <Badge>Dim: {chunk.embedding_dimension}</Badge>
                  )}
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="prose prose-sm max-w-none dark:prose-invert">
                  <pre className="whitespace-pre-wrap text-xs bg-background p-3 rounded border">
                    {chunk.content}
                  </pre>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      ) : (
        <div className="text-sm text-muted-foreground text-center py-4">
          No chunks available for this document.
        </div>
      )}
    </div>
  );
}
