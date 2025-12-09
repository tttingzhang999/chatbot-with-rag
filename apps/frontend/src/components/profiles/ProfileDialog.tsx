import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useProfileStore } from '@/stores/profileStore';
import type { PromptProfile, ProfileCreateRequest, ProfileUpdateRequest } from '@/types/profile';
import { toast } from 'sonner';

interface ProfileDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profile: PromptProfile | null;
  onSuccess: () => void;
}

type FormData = ProfileCreateRequest;

const DEFAULT_SYSTEM_PROMPT = `You are a helpful AI assistant. Provide clear, accurate, and concise responses to user questions.`;

const DEFAULT_RAG_SYSTEM_PROMPT = `You are a helpful AI assistant with access to relevant documents.

Context from documents:
{context}

Based on the above context and your knowledge, provide clear and accurate answers to the user's questions. If the context is relevant, cite it in your response. If the context doesn't contain relevant information, rely on your general knowledge.`;

const LLM_MODEL_OPTIONS = [
  { value: 'amazon.nova-lite-v1:0', label: 'Amazon Nova Lite v1' },
  { value: 'anthropic.claude-3-5-sonnet-20240620-v1:0', label: 'Claude 3.5 Sonnet' },
  { value: 'anthropic.claude-3-haiku-20240307-v1:0', label: 'Claude 3 Haiku' },
] as const;

export function ProfileDialog({ open, onOpenChange, profile, onSuccess }: ProfileDialogProps) {
  const { createProfile, updateProfile, isLoading } = useProfileStore();
  const isEditMode = !!profile;

  const form = useForm<FormData>({
    defaultValues: {
      name: '',
      description: '',
      system_prompt: DEFAULT_SYSTEM_PROMPT,
      rag_system_prompt_template: DEFAULT_RAG_SYSTEM_PROMPT,
      chunk_size: 512,
      chunk_overlap: 50,
      top_k_chunks: 5,
      semantic_search_ratio: 0.5,
      relevance_threshold: 0.5,
      llm_model_id: 'amazon.nova-lite-v1:0',
      llm_temperature: 0.7,
      llm_top_p: 0.9,
      llm_max_tokens: 2048,
    },
  });

  useEffect(() => {
    if (profile) {
      form.reset({
        name: profile.name,
        description: profile.description || '',
        system_prompt: profile.system_prompt,
        rag_system_prompt_template: profile.rag_system_prompt_template,
        chunk_size: profile.chunk_size,
        chunk_overlap: profile.chunk_overlap,
        top_k_chunks: profile.top_k_chunks,
        semantic_search_ratio: profile.semantic_search_ratio,
        relevance_threshold: profile.relevance_threshold,
        llm_model_id: profile.llm_model_id,
        llm_temperature: profile.llm_temperature,
        llm_top_p: profile.llm_top_p,
        llm_max_tokens: profile.llm_max_tokens,
      });
    } else {
      form.reset({
        name: '',
        description: '',
        system_prompt: DEFAULT_SYSTEM_PROMPT,
        rag_system_prompt_template: DEFAULT_RAG_SYSTEM_PROMPT,
        chunk_size: 512,
        chunk_overlap: 50,
        top_k_chunks: 5,
        semantic_search_ratio: 0.5,
        relevance_threshold: 0.5,
        llm_model_id: 'amazon.nova-lite-v1:0',
        llm_temperature: 0.7,
        llm_top_p: 0.9,
        llm_max_tokens: 2048,
      });
    }
  }, [profile, form]);

  const onSubmit = async (data: FormData) => {
    try {
      // Validate RAG template contains {context}
      if (!data.rag_system_prompt_template.includes('{context}')) {
        toast.error('RAG System Prompt must contain {context} placeholder');
        return;
      }

      if (isEditMode) {
        await updateProfile(profile.id, data as ProfileUpdateRequest);
        toast.success('Profile updated successfully');
      } else {
        await createProfile(data);
        toast.success('Profile created successfully');
      }
      onSuccess();
    } catch (error: any) {
      toast.error(error.message || `Failed to ${isEditMode ? 'update' : 'create'} profile`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditMode ? 'Edit Profile' : 'Create New Profile'}</DialogTitle>
          <DialogDescription>
            {isEditMode
              ? 'Update your profile configuration including prompts, RAG settings, and LLM parameters.'
              : 'Create a new profile with custom prompts, RAG settings, and LLM parameters.'}
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic</TabsTrigger>
                <TabsTrigger value="prompts">Prompts</TabsTrigger>
                <TabsTrigger value="rag">RAG Settings</TabsTrigger>
                <TabsTrigger value="llm">LLM Settings</TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4 mt-4">
                <FormField
                  control={form.control}
                  name="name"
                  rules={{
                    required: 'Profile name is required',
                    maxLength: { value: 100, message: 'Name must be less than 100 characters' },
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Profile Name</FormLabel>
                      <FormControl>
                        <Input placeholder="My RAG Profile" {...field} />
                      </FormControl>
                      <FormDescription>
                        A descriptive name for this profile
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description (Optional)</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Describe the purpose of this profile..."
                          rows={3}
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Help identify when to use this profile
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <TabsContent value="prompts" className="space-y-4 mt-4">
                <FormField
                  control={form.control}
                  name="system_prompt"
                  rules={{ required: 'System prompt is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Base System Prompt</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Enter the system prompt..."
                          rows={6}
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Used when no documents are retrieved (general conversation)
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="rag_system_prompt_template"
                  rules={{
                    required: 'RAG system prompt template is required',
                    validate: (value) =>
                      value.includes('{context}') || 'Must contain {context} placeholder',
                  }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>RAG System Prompt Template</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Enter the RAG template with {context} placeholder..."
                          rows={8}
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Used when documents are retrieved. Must include {'{context}'} placeholder
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>

              <TabsContent value="rag" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="chunk_size"
                    rules={{
                      required: 'Chunk size is required',
                      min: { value: 100, message: 'Minimum chunk size is 100' },
                      max: { value: 2000, message: 'Maximum chunk size is 2000' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Chunk Size</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Characters per chunk (100-2000)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="chunk_overlap"
                    rules={{
                      required: 'Chunk overlap is required',
                      min: { value: 0, message: 'Minimum overlap is 0' },
                      max: { value: 500, message: 'Maximum overlap is 500' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Chunk Overlap</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Overlapping characters (0-500)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="top_k_chunks"
                    rules={{
                      required: 'Top K chunks is required',
                      min: { value: 1, message: 'Minimum is 1' },
                      max: { value: 20, message: 'Maximum is 20' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Top K Chunks</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Number of chunks to retrieve (1-20)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="semantic_search_ratio"
                    rules={{
                      required: 'Semantic search ratio is required',
                      min: { value: 0, message: 'Minimum is 0' },
                      max: { value: 1, message: 'Maximum is 1' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Semantic Search Ratio</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.1"
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          0.0 = BM25 only, 1.0 = Semantic only
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="relevance_threshold"
                    rules={{
                      required: 'Relevance threshold is required',
                      min: { value: 0, message: 'Minimum is 0' },
                      max: { value: 1, message: 'Maximum is 1' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Relevance Threshold</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.1"
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Minimum similarity score (0.0-1.0)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </TabsContent>

              <TabsContent value="llm" className="space-y-4 mt-4">
                <FormField
                  control={form.control}
                  name="llm_model_id"
                  rules={{ required: 'LLM model is required' }}
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>LLM Model</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select a model" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {LLM_MODEL_OPTIONS.map((option) => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Select the LLM model to use for chat responses
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="llm_temperature"
                    rules={{
                      required: 'Temperature is required',
                      min: { value: 0, message: 'Minimum is 0' },
                      max: { value: 1, message: 'Maximum is 1' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Temperature</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.1"
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Randomness (0.0-1.0)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="llm_top_p"
                    rules={{
                      required: 'Top P is required',
                      min: { value: 0, message: 'Minimum is 0' },
                      max: { value: 1, message: 'Maximum is 1' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Top P</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            step="0.1"
                            {...field}
                            onChange={(e) => field.onChange(parseFloat(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Nucleus sampling (0.0-1.0)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="llm_max_tokens"
                    rules={{
                      required: 'Max tokens is required',
                      min: { value: 100, message: 'Minimum is 100' },
                      max: { value: 8192, message: 'Maximum is 8192' },
                    }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Max Tokens</FormLabel>
                        <FormControl>
                          <Input
                            type="number"
                            {...field}
                            onChange={(e) => field.onChange(parseInt(e.target.value))}
                          />
                        </FormControl>
                        <FormDescription>
                          Response length (100-8192)
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isLoading}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isEditMode ? 'Update Profile' : 'Create Profile'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
