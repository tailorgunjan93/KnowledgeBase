import React, { useState, useEffect, useRef } from 'react';
import { kbAPI } from '../api';

const FILE_ICONS = { pdf: '📄', doc: '📝', docx: '📝', txt: '📃', xlsx: '📊', xls: '📊' };
const ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'txt', 'xlsx', 'xls'];

/* ===== format helpers ===== */
function formatDate(dateString) {
  if (!dateString) return '—';
  const d = new Date(dateString);
  return isNaN(d) ? '—' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}
function formatSize(bytes) {
  if (bytes == null) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function KnowledgeBasePage({ user }) {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB, setSelectedKB] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDesc, setNewKBDesc] = useState('');
  const [showNewKB, setShowNewKB] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => { fetchKBs(); }, []);

  const fetchKBs = async () => {
    try {
      const res = await kbAPI.list();
      setKnowledgeBases(res.data.items || []);
    } catch (err) { console.error('Failed to fetch KBs'); }
  };

  const createKB = async () => {
    if (!newKBName.trim()) return;
    try {
      await kbAPI.create(newKBName, newKBDesc);
      setNewKBName(''); setNewKBDesc(''); setShowNewKB(false);
      fetchKBs();
    } catch (err) { console.error('Failed to create KB'); }
  };

  const deleteKB = async (kbId) => {
    if (!confirm('Delete this knowledge base?')) return;
    try {
      await kbAPI.delete(kbId);
      if (selectedKB === kbId) { setSelectedKB(null); setDocuments([]); }
      fetchKBs();
    } catch (err) { console.error('Failed to delete KB'); }
  };

  const selectKB = async (kbId) => {
    setSelectedKB(kbId);
    try {
      const res = await kbAPI.getDocuments(kbId);
      setDocuments(res.data.items || []);
    } catch (err) { console.error('Failed to fetch documents'); }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleUpload = async (file) => {
    if (!file || !selectedKB) return;

    // Validate file type
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      setError(`Unsupported file type (.${ext}). Allowed: ${ALLOWED_TYPES.join(', ')}`);
      return;
    }

    setUploading(true);
    setUploadPercent(0);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      await kbAPI.uploadDocument(selectedKB, formData);
      await selectKB(selectedKB);
    } catch (err) {
      console.error('Failed to upload document:', err);
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
      setUploadPercent(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const deleteDoc = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await kbAPI.deleteDocument(docId);
      selectKB(selectedKB);
    } catch (err) { console.error('Failed to delete document'); }
  };

  const selectedKBObj = knowledgeBases.find(k => k.id === selectedKB);

  return (
    <div className="kb-layout">
      {/* ── Left sidebar ── */}
      <div className="threads">
        <div className="threads-head">
          <button className="btn-new" onClick={() => setShowNewKB(!showNewKB)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            Create KB
          </button>

          {showNewKB && (
            <form className="kb-create-form" onSubmit={e => { e.preventDefault(); createKB(); }}>
              <input type="text" placeholder="Name" value={newKBName} onChange={e => setNewKBName(e.target.value)} required />
              <input type="text" placeholder="Description (optional)" value={newKBDesc} onChange={e => setNewKBDesc(e.target.value)} />
              <div className="kb-create-actions">
                <button type="submit">Save</button>
                <button type="button" className="ghost" onClick={() => setShowNewKB(false)}>Cancel</button>
              </div>
            </form>
          )}
        </div>

        <div className="threads-list">
          <div className="thread-date-label">Your Knowledge Bases</div>
          {knowledgeBases.map(kb => (
            <div key={kb.id} className={`thread-item ${selectedKB === kb.id ? 'active' : ''}`} onClick={() => selectKB(kb.id)}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <div className="thread-title">{kb.name}</div>
                <button className="kb-del-btn" onClick={(e) => { e.stopPropagation(); deleteKB(kb.id); }}>×</button>
              </div>
              <div className="thread-meta">{kb.document_count || 0} docs</div>
            </div>
          ))}
          {knowledgeBases.length === 0 && <div className="kb-empty-msg">No Knowledge Bases found.</div>}
        </div>
      </div>

      {/* ── Main content ── */}
      <div className="kb-content">
        {selectedKB ? (
          <>
            {/* Header */}
            <div className="kb-header">
              <h2>{selectedKBObj?.name || 'Documents'}</h2>
              {selectedKBObj?.description && <p className="kb-desc">{selectedKBObj.description}</p>}
            </div>

            {error && <div className="error-message">{error}</div>}

            {/* Upload zone */}
            <div
              className={`upload-form ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => !uploading && fileInputRef.current?.click()}
            >
              {uploading ? (
                <LoadingSpinner text="Uploading…" />
              ) : (
                <>
                  <div className="upload-icon">{dragOver ? '🚀' : '📁'}</div>
                  <div className="upload-text">Drop files here or click to browse</div>
                  <div className="upload-hint">PDF, DOCX, TXT, XLSX supported</div>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                onChange={e => handleUpload(e.target.files[0])}
                disabled={uploading}
              />
            </div>

            {/* Documents list */}
            <div className="documents-list">
              {documents.length === 0 && (
                <div className="kb-doc-empty">
                  <span className="kb-doc-empty-icon">📂</span>
                  <p>No documents yet.<br />Upload one above to get started.</p>
                </div>
              )}
              {documents.map(doc => (
                <div key={doc.id} className="document-item">
                  <div className="doc-info">
                    <span className="doc-icon">{FILE_ICONS[doc.file_type] || '📄'}</span>
                    <div className="doc-details">
                      <span className="doc-title" title={doc.title}>{doc.title}</span>
                      <span className="doc-meta">{formatDate(doc.created_at)} · {formatSize(doc.size)}</span>
                    </div>
                  </div>
                  <StatusBadge status={doc.index_status} />
                  <button className="doc-del-btn" onClick={() => deleteDoc(doc.id)} title="Delete document">×</button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">📚</div>
            <p className="empty-title">Knowledge Base</p>
            <p className="empty-sub">Select a knowledge base from the left to view and manage its documents.</p>
          </div>
        )}
      </div>
    </div>
  );
}

/* ===== sub-components ===== */
function LoadingSpinner({ text }) {
  return (
    <div className="upload-spinner-wrap">
      <div className="upload-spinner" />
      <div className="upload-spinner-text">{text}</div>
    </div>
  );
}

function StatusBadge({ status }) {
  let cls = 'pending';
  if (status === 'indexed') cls = 'indexed';
  if (status === 'indexing') cls = 'indexing';
  if (status === 'failed' || status === 'error') cls = 'failed';
  return <span className={`status ${cls}`}>{status || 'pending'}</span>;
}