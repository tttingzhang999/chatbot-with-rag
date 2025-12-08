import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer = ({ content }: MarkdownRendererProps) => {
  const components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || '');
      const codeString = String(children).replace(/\n$/, '');

      return !inline && match ? (
        <div className="relative group overflow-x-auto">
          <SyntaxHighlighter
            style={oneDark}
            language={match[1]}
            PreTag="div"
            className="rounded-md my-2"
            {...props}
          >
            {codeString}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
          {children}
        </code>
      );
    },
    a({ href, children, ...props }: any) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline"
          {...props}
        >
          {children}
        </a>
      );
    },
    p({ children, ...props }: any) {
      return (
        <p className="mb-4 last:mb-0" {...props}>
          {children}
        </p>
      );
    },
    ul({ children, ...props }: any) {
      return (
        <ul className="list-disc list-inside mb-4 space-y-1" {...props}>
          {children}
        </ul>
      );
    },
    ol({ children, ...props }: any) {
      return (
        <ol className="list-decimal list-inside mb-4 space-y-1" {...props}>
          {children}
        </ol>
      );
    },
    blockquote({ children, ...props }: any) {
      return (
        <blockquote
          className="border-l-4 border-muted-foreground/20 pl-4 italic my-4"
          {...props}
        >
          {children}
        </blockquote>
      );
    },
    h1({ children, ...props }: any) {
      return (
        <h1 className="text-2xl font-bold mt-6 mb-4" {...props}>
          {children}
        </h1>
      );
    },
    h2({ children, ...props }: any) {
      return (
        <h2 className="text-xl font-bold mt-5 mb-3" {...props}>
          {children}
        </h2>
      );
    },
    h3({ children, ...props }: any) {
      return (
        <h3 className="text-lg font-bold mt-4 mb-2" {...props}>
          {children}
        </h3>
      );
    },
    table({ children, ...props }: any) {
      return (
        <div className="overflow-x-auto my-4">
          <table className="border-collapse border border-border w-full" {...props}>
            {children}
          </table>
        </div>
      );
    },
    th({ children, ...props }: any) {
      return (
        <th className="border border-border px-4 py-2 bg-muted font-semibold" {...props}>
          {children}
        </th>
      );
    },
    td({ children, ...props }: any) {
      return (
        <td className="border border-border px-4 py-2" {...props}>
          {children}
        </td>
      );
    },
  };

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown components={components}>{content}</ReactMarkdown>
    </div>
  );
};
