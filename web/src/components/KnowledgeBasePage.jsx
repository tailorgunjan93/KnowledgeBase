import React, { useState, useEffect } from 'react';
import { kbAPI } from '../api';

export function KnowledgeBasePage({ user }) {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDesc, setNewKBDesc] = useState('');
  const [showNewKB, setShowNewKB] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [newDocFile, setNewDocFile] = useState(null);

  useEffect(() => {
    fetchKnowledgeBases();
  }, []);

  const fetchKnowledgeBases = async () => {
    try {
      const res = await kbAPI.list();
      setKnowledgeBases(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch KBs');
    }
  };

  const createKB = async () => {
    if (!newKBName.trim()) return;
    try {
      await kbAPI.create(newKBName, newKBDesc);
      setNewKBName('');
      setNewKBDesc('');
      setShowNewKB(false);
      fetchKnowledgeBases();
    } catch (err) {
      console.error('Failed to create KB');
    }
  };

  const deleteKB = async (kbId) => {
    if (!confirm('Delete this knowledge base?')) return;
    try {
      await kbAPI.delete(kbId);
      if (selectedKB === kbId) setSelectedKB(null);
      fetchKnowledgeBases();
    } catch (err) {
      console.error('Failed to delete KB');
    }
  };

  const selectKB = async (kbId) => {
    setSelectedKB(kbId);
    try {
      const res = await kbAPI.getDocuments(kbId);
      setDocuments(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch documents');
    }
  };

  const uploadDocument = async () => {
    if (!newDocFile || !selectedKB) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', newDocFile);
      await kbAPI.uploadDocument(selectedKB, formData);
      setNewDocFile(null);
      // Reset file input visually
      document.getElementById('kb-file-input').value = '';
      selectKB(selectedKB);
    } catch (err) {
      console.error('Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const deleteDocument = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await kbAPI.deleteDocument(docId);
      if (selectedKB) selectKB(selectedKB);
    } catch (err) {
      console.error('Failed to delete document');
    }
  };

  return (
    <div className="kb-page">
      <h1>Knowledge Base</h1>

      <div className="kb-container">
        <div className="kb-list">
          <button className="create-kb-btn" onClick={() => setShowNewKB(true)}>+ Create Knowledge Base</button>

          {showNewKB && (
            <div className="new-kb-form">
              <input
                type="text"
                placeholder="KB Name"
                value={newKBName}
                onChange={(e) => setNewKBName(e.target.value)}
              />
              <input
                type="text"
                placeholder="Description"
                value={newKBDesc}
                onChange={(e) => setNewKBDesc(e.target.value)}
              />
              <button onClick={createKB}>Create</button>
              <button onClick={() => setShowNewKB(false)} className="cancel-btn">Cancel</button>
            </div>
          )}

          {knowledgeBases.map(kb => (
            <div
              key={kb.id}
              className={`kb-item ${kb.id === selectedKB ? 'active' : ''}`}
              onClick={() => selectKB(kb.id)}
            >
              <span>{kb.name}</span>
              <button
                className="delete-btn"
                onClick={(e) => { e.stopPropagation(); deleteKB(kb.id); }}
              >×</button>
            </div>
          ))}
        </div>

        <div className="kb-content">
          {selectedKB ? (
            <>
              <h2>Documents in Knowledge Base</h2>
              <div className="upload-form">
                <input
                  id="kb-file-input"
                  type="file"
                  onChange={(e) => setNewDocFile(e.target.files[0])}
                />
                <button
                  onClick={uploadDocument}
                  disabled={uploading || !newDocFile}
                >
                  {uploading ? 'Uploading...' : 'Add Document'}
                </button>
              </div>

              <div className="documents-list">
                {documents.map(doc => (
                  <div key={doc.id} className="document-item">
                    <span>{doc.title}</span>
                    <span className={`status ${doc.indexed ? 'indexed' : ''}`}>
                      {doc.index_status}
                    </span>
                    <button className="delete-btn" onClick={() => deleteDocument(doc.id)}>×</button>
                  </div>
                ))}
                {documents.length === 0 && <p>No documents yet.</p>}
              </div>
            </>
          ) : (
            <p className="select-prompt">Select a knowledge base to view documents</p>
          )}
        </div>
      </div>
    </div>
  );
}