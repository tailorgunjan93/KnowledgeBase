import React, { useState, useEffect, useRef, useCallback } from 'react';
import { listKnowledgeBases, getKnowledgeBase, createKnowledgeBase, deleteKnowledgeBase, getDocuments, uploadDocument, deleteDocument } from '../api/documentApi';
import DropZone from '../components/DropZone';

const FILE_ICONS = { pdf: '📄', doc: '📝', docx: '📝', txt: '📃', md: '📃', xlsx: '📊', xls: '📊' };
const ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'txt', 'md', 'xlsx', 'xls'];

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
  const [error, setError] = useState('');

  useEffect(() => { 
    fetchKBs(); 
  }, []);

  const fetchKBs = async () => {
    try {
      const { data } = await listKnowledgeBases();
      setKnowledgeBases(data.items || []);
    } catch (err) { console.error('Failed to fetch KBs'); }
  };

  const handleCreateKB = async (e) => {
    e.preventDefault();
    if (!newKBName.trim()) return;
    try {
      await createKnowledgeBase(newKBName, newKBDesc);
      setNewKBName(''); 
      setNewKBDesc(''); 
      setShowNewKB(false);
      fetchKBs();
    } catch (err) { console.error('Failed to create KB'); }
  };

  const handleDeleteKB = async (kbId) => {
    if (!confirm('Delete this knowledge base? All documents inside will be lost.')) return;
    try {
      await deleteKnowledgeBase(kbId);
      if (selectedKB === kbId) { setSelectedKB(null); setDocuments([]); }
      fetchKBs();
    } catch (err) { console.error('Failed to delete KB'); }
  };

  const selectKB = useCallback(async (kbId) => {
    setSelectedKB(kbId);
    try {
      const { data } = await getDocuments(kbId);
      setDocuments(data.items || []);
    } catch (err) { console.error('Failed to fetch documents'); }
  }, []);

  const onFilesDropped = (files) => {
    if (files && files.length > 0) {
      handleUpload(files[0]);
    }
  };

  const handleUpload = async (file) => {
    if (!file || !selectedKB) return;

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
      
      await uploadDocument(selectedKB, formData, (percent) => {
        setUploadPercent(percent);
      });
      
      // Refresh documents
      await selectKB(selectedKB);
      fetchKBs(); // Update doc count
    } catch (err) {
      console.error('Failed to upload document:', err);
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
      setUploadPercent(0);
    }
  };

  const handleDeleteDoc = async (docId) => {
    if (!confirm('Delete this document?')) return;
    try {
      await deleteDocument(docId);
      selectKB(selectedKB);
    } catch (err) { console.error('Failed to delete document'); }
  };

  const selectedKBObj = knowledgeBases.find(k => k.id === selectedKB);

  return (
    <div className="kb-layout">
      <div className="threads">
        <div className="threads-head">
          <button className="btn-new" onClick={() => setShowNewKB(!showNewKB)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
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
          {knowledgeBases.map(kb => (
            <div key={kb.id} className={`thread-item ${selectedKB === kb.id ? 'active' : ''}`} onClick={() => selectKB(kb.id)}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%'}}>
                <div className="thread-title">{kb.name}</div>
                <button className="kb-del-btn" onClick={(e) => { e.stopPropagation(); handleDeleteKB(kb.id); }} style={{background:'none', border:'none', cursor:'pointer', fontSize:'18px', opacity:0.5}}>×</button>
              </div>
              <div className="thread-meta">{kb.document_count || 0} documents</div>
            </div>
          ))}
          {knowledgeBases.length === 0 && <div style={{padding: 'var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)'}}>No Knowledge Bases found.</div>}
        </div>
      </div>

      <div className="kb-content" style={{ padding: 'var(--space-8)' }}>
        {selectedKB ? (
          <>
            <div className="kb-header" style={{ marginBottom: 'var(--space-8)' }}>
              <h2 style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, margin: 0 }}>{selectedKBObj?.name}</h2>
              {selectedKBObj?.description && <p style={{ color: 'var(--color-text-muted)', marginTop: 'var(--space-2)' }}>{selectedKBObj.description}</p>}
            </div>

            {error && <div style={{ color: 'var(--color-error)', background: '#FEE2E2', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', marginBottom: 'var(--space-4)' }}>{error}</div>}

            <div style={{ marginBottom: 'var(--space-8)' }}>
              <DropZone onFiles={onFilesDropped} disabled={uploading} />
              
              {uploading && (
                <div style={{ marginTop: 'var(--space-4)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', marginBottom: '4px' }}>
                    <span>Uploading...</span>
                    <span>{uploadPercent}%</span>
                  </div>
                  <div style={{ height: '6px', background: 'var(--color-border)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', background: 'var(--color-primary)', width: `${uploadPercent}%`, transition: 'width 0.2s ease' }}></div>
                  </div>
                </div>
              )}
            </div>

            <div className="documents-list">
              <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 600, marginBottom: 'var(--space-4)' }}>Documents</h3>
              {documents.length === 0 && (
                <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--color-text-muted)' }}>
                  <p>No documents yet. Upload one above to get started.</p>
                </div>
              )}
              {documents.map(doc => (
                <div key={doc.id} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  padding: 'var(--space-4)', 
                  background: 'var(--color-surface)', 
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  marginBottom: 'var(--space-2)',
                  boxShadow: 'var(--shadow-sm)'
                }}>
                  <div style={{ fontSize: '24px', marginRight: 'var(--space-4)' }}>
                    {FILE_ICONS[doc.file_type] || '📄'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 'var(--text-base)' }}>{doc.title}</div>
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                      {formatDate(doc.created_at)} · {formatSize(doc.size)}
                    </div>
                  </div>
                  <StatusBadge status={doc.index_status} />
                  <button 
                    onClick={() => handleDeleteDoc(doc.id)} 
                    style={{ background:'none', border:'none', cursor:'pointer', fontSize:'20px', marginLeft:'var(--space-4)', opacity:0.5 }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
            <div style={{ fontSize: '48px', marginBottom: 'var(--space-4)' }}>📚</div>
            <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 700 }}>Select a Knowledge Base</h2>
            <p style={{ color: 'var(--color-text-muted)' }}>Choose one from the left to manage your documents.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    indexed: { bg: '#D1FAE5', text: '#065F46' },
    indexing: { bg: '#DBEAFE', text: '#1E40AF' },
    pending: { bg: '#F3F4F6', text: '#374151' },
    failed: { bg: '#FEE2E2', text: '#991B1B' }
  };
  const theme = colors[status] || colors.pending;
  return (
    <span style={{
      background: theme.bg,
      color: theme.text,
      padding: '2px 8px',
      borderRadius: 'var(--radius-sm)',
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      textTransform: 'capitalize'
    }}>
      {status || 'pending'}
    </span>
  );
}