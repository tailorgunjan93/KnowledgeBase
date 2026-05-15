import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import katex from 'katex';
import 'katex/dist/katex.min.css';

/* ─────────────────────────────────────────────────────────────────
   STEP 1 — normalise non-standard delimiters LLMs commonly emit
─────────────────────────────────────────────────────────────────── */
function normaliseMathDelimiters(text) {
  // [ \LaTeX ] → $$\LaTeX$$   (LLM omits backslash before \[)
  text = text.replace(
    /\[\s*((?:[^\[\]])*\\[a-zA-Z{(][^\[\]]*)\s*\](?!\(|\[)/g,
    (_, inner) => `$$${inner.trim()}$$`,
  );
  // \[ ... \] → $$...$$
  text = text.replace(/\\\[\s*([\s\S]*?)\s*\\\]/g, (_, f) => `$$${f.trim()}$$`);
  // \( ... \) → $...$
  text = text.replace(/\\\(\s*([\s\S]*?)\s*\\\)/g, (_, f) => `$${f.trim()}$`);
  return text;
}

/* ─────────────────────────────────────────────────────────────────
   STEP 2 — pre-render math to KaTeX HTML before ReactMarkdown sees it.
   We do this in JS (not via remark-math/rehype-katex plugins) so that
   it works regardless of react-markdown version.
─────────────────────────────────────────────────────────────────── */
function renderKatex(formula, display) {
  try {
    return katex.renderToString(formula.trim(), {
      displayMode: display,
      throwOnError: false,
      output: 'html',
      trust: false,
    });
  } catch {
    // If KaTeX can't parse it, return the raw formula so it's still readable
    return `<code class="math-error">${formula}</code>`;
  }
}

/* ─────────────────────────────────────────────────────────────────
   STEP 3 — fix stray HTML tags the LLM drops inside table cells, etc.
─────────────────────────────────────────────────────────────────── */
function fixBrokenHtml(text) {
  // </br> is invalid HTML — convert to a markdown line-break (two spaces + newline)
  text = text.replace(/<\/br>/gi, '  \n');
  // <br/> or <br /> inside table cells → space (tables can't contain block elements)
  text = text.replace(/<br\s*\/?>/gi, ' ');
  return text;
}

/* ─────────────────────────────────────────────────────────────────
   Master preprocessor — runs before ReactMarkdown
─────────────────────────────────────────────────────────────────── */
function processContent(raw) {
  if (!raw) return '';
  let text = normaliseMathDelimiters(raw);
  text = fixBrokenHtml(text);

  // Render $$display$$ blocks
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, formula) => {
    const html = renderKatex(formula, true);
    return `<span class="math-display-wrap">${html}</span>`;
  });

  // Render $inline$ (not preceded or followed by another $, not multi-line)
  text = text.replace(/(?<!\$)\$([^$\n]{1,300}?)\$(?!\$)/g, (match, formula) => {
    // Skip if it looks like a currency amount (e.g., $500 or $5.99)
    if (/^\d/.test(formula.trim())) return match;
    const html = renderKatex(formula, false);
    return `<span class="math-inline-wrap">${html}</span>`;
  });

  return text;
}

/* ─────────────────────────────────────────────────────────────────
   MarkdownRenderer component
─────────────────────────────────────────────────────────────────── */
export function MarkdownRenderer({ content, className = '' }) {
  const processed = processContent(content);

  return (
    <div className={`md-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Links — open in new tab
          a: ({ node, href, children, ...props }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
              {children}
            </a>
          ),

          // react-markdown v10: code no longer has an `inline` prop.
          // Block code lives inside <pre>; inline code does not.
          pre: ({ node, children, ...props }) => (
            <div className="md-code-block">
              <pre {...props}>{children}</pre>
            </div>
          ),
          code: ({ node, className: cls, children, ...props }) => {
            const lang = cls?.replace('language-', '') || '';
            // If rendered inside our <pre> wrapper it's a block; otherwise inline
            const isBlock = !!cls;
            if (isBlock) {
              return (
                <>
                  {lang && <div className="md-code-lang">{lang}</div>}
                  <code className={cls} {...props}>{children}</code>
                </>
              );
            }
            return <code className="md-inline-code" {...props}>{children}</code>;
          },

          // Tables
          table:   ({ node, ...props }) => (
            <div className="md-table-wrap"><table {...props} /></div>
          ),
          th: ({ node, ...props }) => <th {...props} />,
          td: ({ node, ...props }) => <td {...props} />,

          // Blockquotes
          blockquote: ({ node, ...props }) => (
            <blockquote className="md-blockquote" {...props} />
          ),

          // Headers (scaled for chat bubble context)
          h1: ({ node, ...props }) => <h1 className="md-h1" {...props} />,
          h2: ({ node, ...props }) => <h2 className="md-h2" {...props} />,
          h3: ({ node, ...props }) => <h3 className="md-h3" {...props} />,
          h4: ({ node, ...props }) => <h4 className="md-h4" {...props} />,

          // Lists
          ul: ({ node, ...props }) => <ul className="md-ul" {...props} />,
          ol: ({ node, ...props }) => <ol className="md-ol" {...props} />,
          li: ({ node, ...props }) => <li className="md-li" {...props} />,

          // Paragraphs, rules, strong
          p:      ({ node, ...props }) => <p  className="md-p"  {...props} />,
          hr:     ({ node, ...props }) => <hr className="md-hr" {...props} />,
          strong: ({ node, ...props }) => <strong className="md-strong" {...props} />,
        }}
      >
        {processed}
      </ReactMarkdown>
    </div>
  );
}
