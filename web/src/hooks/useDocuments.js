import { useState, useEffect, useCallback } from 'react';
import { listKnowledgeBases } from '../api/documentApi';

// ── Module-level cache ──────────────────────────────────────────────────────
// Shared across all hook instances — survives component remounts so the chat
// dropdown and KB page both show data instantly on re-navigation.
let _cached = [];
let _lastFetch = 0;
const STALE_MS = 30_000; // re-fetch after 30 s of staleness

/** Force-expire the cache (call after create / delete mutations). */
export function invalidateKBCache() {
  _cached = [];
  _lastFetch = 0;
}

export function useDocuments() {
  // Initialise from cache immediately — no empty-flash on remount
  const [knowledgeBases, setKnowledgeBases] = useState(_cached);
  const [loading, setLoading] = useState(_cached.length === 0);
  const [error, setError] = useState(null);

  const fetchKBs = useCallback(async (force = false) => {
    const age = Date.now() - _lastFetch;
    // Serve from cache when fresh and not explicitly forced
    if (!force && _cached.length > 0 && age < STALE_MS) {
      setKnowledgeBases(_cached);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await listKnowledgeBases();
      _cached = data.items || [];
      _lastFetch = Date.now();
      setKnowledgeBases(_cached);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKBs();
  }, [fetchKBs]);

  // refresh(true) bypasses cache — use after mutations
  return { knowledgeBases, loading, error, refresh: (force = true) => fetchKBs(force) };
}
