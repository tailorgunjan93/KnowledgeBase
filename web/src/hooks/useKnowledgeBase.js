import { useState, useCallback } from 'react';
import { kbAPI } from '../api';

export function useKnowledgeBase() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchKnowledgeBases = useCallback(async () => {
    try {
      const res = await kbAPI.list();
      setKnowledgeBases(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch KBs');
    }
  }, []);

  const createKB = useCallback(async (name, description) => {
    try {
      await kbAPI.create(name, description);
      fetchKnowledgeBases();
    } catch (err) {
      console.error('Failed to create KB');
    }
  }, [fetchKnowledgeBases]);

  const deleteKB = useCallback(async (kbId) => {
    try {
      await kbAPI.delete(kbId);
      if (selectedKB === kbId) setSelectedKB(null);
      fetchKnowledgeBases();
    } catch (err) {
      console.error('Failed to delete KB');
    }
  }, [selectedKB, fetchKnowledgeBases]);

  const selectKB = useCallback(async (kbId) => {
    setSelectedKB(kbId);
    try {
      const res = await kbAPI.getDocuments(kbId);
      setDocuments(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch documents');
    }
  }, []);

  const uploadDocument = useCallback(async (kbId, title, content) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', new Blob([content], { type: 'text/plain' }), `${title}.txt`);

      // Use raw axios for file upload since our API wrapper doesn't handle FormData well
      import axios from 'axios';
      const { API_URL } = await import('../api/client');
      const token = sessionStorage.getItem('auth_token');

      await axios.post(`${API_URL}/api/kb/${kbId}/documents`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      selectKB(kbId);
    } catch (err) {
      console.error('Failed to upload document');
    } finally {
      setLoading(false);
    }
  }, [selectKB]);

  const deleteDocument = useCallback(async (docId) => {
    try {
      await kbAPI.deleteDocument(docId);
      if (selectedKB) selectKB(selectedKB);
    } catch (err) {
      console.error('Failed to delete document');
    }
  }, [selectedKB, selectKB]);

  return {
    knowledgeBases,
    selectedKB,
    documents,
    loading,
    fetchKnowledgeBases,
    createKB,
    deleteKB,
    selectKB,
    uploadDocument,
    deleteDocument,
  };
}