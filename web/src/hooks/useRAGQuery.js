import { useState, useCallback } from 'react';
import { ragQuery } from '../api/ragApi';

export function useRAGQuery() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const query = useCallback(async (queryText, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await ragQuery({ 
        message: queryText, 
        session_id: options.session_id,
        kb_ids: options.kb_ids,
        enable_web_search: options.enable_web_search
      });
      setResult(data);
      return data;
    } catch (err) {
      const msg = err.message || 'Summarization failed';
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { query, result, loading, error };
}
