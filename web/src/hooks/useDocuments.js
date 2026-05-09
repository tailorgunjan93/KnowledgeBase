import { useState, useEffect, useCallback } from 'react';
import { listKnowledgeBases } from '../api/documentApi';

export function useDocuments() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchKBs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await listKnowledgeBases();
      setKnowledgeBases(data.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKBs();
  }, [fetchKBs]);

  return { knowledgeBases, loading, error, refresh: fetchKBs };
}
