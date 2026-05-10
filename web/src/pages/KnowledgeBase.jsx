import { useState, useEffect, useCallback } from 'react';
import { listKnowledgeBases, createKnowledgeBase, deleteKnowledgeBase, getDocuments, uploadDocument, deleteDocument } from '../api/documentApi';
import DropZone from '../components/DropZone';

const FILE_ICONS = { pdf: '📄', doc: '📝', docx: '📝', txt: '📃', md: '📃', xlsx: '📊', xls: '📊' };
const ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'txt', 'md', 'xlsx', 'xls'];

function formatDate(s) {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d) ? '—' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function StatusBadge({ status }) {
  const cls = { indexed: 'indexed', indexing: 'indexing', pending: 'pending', failed: 'failed' }[status] || 'pending';
  return <span className={`status-badge status-${cls}`}>{status || 'pending'}</span>;
}

export function KnowledgeBasePage() {
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [selectedKB,     setSelectedKB]     = useState(null);
  const [documents,      setDocuments]      = useState([]);
  const [newKBName,      setNewKBName]      = useState('');
  const [newKBDesc,      setNewKBDesc]      = useState('');
  const [showNewKB,      setShowNewKB]      = useState(false);
  const [uploading,      setUploading]      = useState(false);
  const [uploadPercent,  setUploadPercent]  = useState(0);
  const [error,          setError]          = useState('');

  useEffect(() => { fetchKBs(); }, []);

  const fetchKBs = async () => {
    try {
      const { data } = await listKnowledgeBases();
      setKnowledgeBases(data.items || []);
    } catch { /* silent */ }
  };

  const handleCreateKB = async (e) => {
    e.preventDefault();
    if (!newKBName.trim()) return;
    try {
      await createKnowledgeBase(newKBName, newKBDesc);
      setNewKBName(''); setNewKBDesc(''); setShowNewKB(false);
      fetchKBs();
    } catch { /* silent */ }
  };

  const handleDeleteKB = async (kbId) => {
    if (!confirm('Delete this knowledge base? All documents inside will be lost.')) return;
    try {
      await deleteKnowledgeBase(kbId);
      if (selectedKB === kbId) { setSelectedKB(null); setDocuments([]); }
      fetchKBs();
    } catch { /* silent */ }
  };

  const selectKB = useCallback(async (kbId) => {
    setSelectedKB(kbId);
    try {
      const { data } = await getDocuments(kbId);
      setDocuments(data.items || []);
    } catch { /* silent */ }
  }, []);

  const handleUpload = async (file) => {
    if (!file || !selectedKB) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_TYPES.includes(ext)) {
      setError(`Unsupported file type (.${ext}). Allowed: ${ALLOWED_TYPES.join(', ')}`);
      return;
    }
    setUploading(true); setUploadPercent(0); setError('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      await uploadDocument(selectedKB, fd, pct => setUploadPercent(pct));
      await selectKB(selectedKB);
      fetchKBs();
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false); setUploadPercent(0);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await deleteDocument(docId);
      selectKB(selectedKB);
    } catch { /* silent */ }
  };

  const selectedKBObj = knowledgeBases.find(k => k.id === selectedKB);

  return (
    <div className="kb-layout">
      {/* Left panel — KB list */}
      <div className="threads">
        <div className="threads-head">
          <button className="btn-new" onClick={() => setShowNewKB(p => !p)}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Create KB
          </button>

          {showNewKB && (
            <form className="kb-create-form" onSubmit={handleCreateKB}>
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

          {knowledgeBases.length === 0 && (
            <div style={{ padding: 'var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-faint)' }}>
              No knowledge bases yet.
            </div>
          )}

          {knowledgeBases.map(kb => (
            <div
              key={kb.id}
              className={`thread-item ${selectedKB === kb.id ? 'active' : ''}`}
              onClick={() => selectKB(kb.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div className="thread-title">{kb.name}</div>
                <button
                  className="kb-del-btn"
                  onClick={e => { e.stopPropagation(); handleDeleteKB(kb.id); }}
                >×</button>
              </div>
              <div className="thread-meta">{kb.document_count || 0} documents</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — documents */}
      <div className="kb-content">
        {selectedKB ? (
          <>
            <div className="kb-page-header">
              <h2>{selectedKBObj?.name}</h2>
              {selectedKBObj?.description && (
                <p>{selectedKBObj.description}</p>
              )}
            </div>

            {error && (
              <div style={{
                color: 'var(--color-error-text)', background: 'var(--color-error-bg)',
                padding: 'var(--space-3) var(--space-4)', borderRadius: 'var(--radius-sm)',
                marginBottom: 'var(--space-4)', border: '1px solid var(--color-error)',
                fontSize: 'var(--text-sm)'
              }}>
                {error}
              </div>
            )}

            <div style={{ marginBottom: 'var(--space-6)' }}>
              <DropZone onFiles={files => files?.[0] && handleUpload(files[0])} disabled={uploading} />

              {uploading && (
                <div style={{ marginTop: 'var(--space-3)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                    <span>Uploading…</span>
                    <span>{uploadPercent}%</span>
                  </div>
                  <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" style={{ width: `${uploadPercent}%` }} />
                  </div>
                </div>
              )}
            </div>

            <div>
              <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: 'var(--space-3)' }}>
                Documents
                <span style={{ marginLeft: 8, fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--color-text-faint)' }}>
                  {documents.length}
                </span>
              </h3>

              {documents.length === 0 && (
                <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--color-text-faint)', fontSize: 'var(--text-sm)' }}>
                  No documents yet. Drop a file above to get started.
                </div>
              )}

              {documents.map(doc => (
                <div key={doc.id} className="doc-item">
                  <div className="doc-icon">
                    {FILE_ICONS[doc.file_type] || '📄'}
                  </div>
                  <div className="doc-info">
                    <div className="doc-title">{doc.title}</div>
                    <div className="doc-meta">
                      {formatDate(doc.created_at)}
                      {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
                    </div>
                  </div>
                  <StatusBadge status={doc.index_status} />
                  <button className="doc-del-btn" onClick={() => handleDeleteDoc(doc.id)}>×</button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state" style={{ height: '100%' }}>
            <div className="empty-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
            </div>
            <p className="empty-title">Select a Knowledge Base</p>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
              Choose one from the left to manage documents, or create a new one.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
