import { useState, useCallback } from 'react';
import { ragQuery } from '../api/ragApi';

export function useRAGQuery() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const query = useCallback(async (queryText, options = {}, onUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const token = sessionStorage.getItem('auth_token');
      const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: queryText,
          session_id: options.session_id,
          kb_ids: options.kb_ids,
          enable_web_search: options.enable_web_search
        })
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Chat failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let metaData = null;

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'status') {
              onUpdate?.({ status: data.content });
            } else if (data.type === 'session') {
              onUpdate?.({ session_id: data.session_id });
            } else if (data.type === 'meta') {
              metaData = data;
              onUpdate?.({ ...data, content: fullText, isMeta: true });
            } else if (data.type === 'content') {
              fullText += data.delta;
              // Only clear status if we actually have non-whitespace content to show
              const hasContent = fullText.trim().length > 0;
              onUpdate?.({ 
                content: fullText, 
                delta: data.delta, 
                status: hasContent ? null : undefined 
              });
            }
          } catch (e) {
            console.error('Error parsing stream chunk', e, line);
          }
        }
      }

      const finalResult = { ...metaData, response: fullText };
      setResult(finalResult);
      return finalResult;
    } catch (err) {
      const msg = err.message || 'Chat failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { query, result, loading, error };
}
