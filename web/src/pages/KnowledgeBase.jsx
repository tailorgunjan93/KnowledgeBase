import { useState, useCallback, useEffect } from 'react';
import { createKnowledgeBase, deleteKnowledgeBase, getDocuments, uploadDocument, deleteDocument,
         listKBMembers, addKBMember, updateKBMember, removeKBMember } from '../api/documentApi';
import { useDocuments } from '../hooks/useDocuments';
import DropZone from '../components/DropZone';

const FILE_ICONS = { pdf: '📄', doc: '📝', docx: '📝', txt: '📃', md: '📃', xlsx: '📊', xls: '📊' };
const ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'txt', 'md', 'xlsx', 'xls'];

const ROLE_LABELS = { owner: 'Owner', editor: 'Editor', viewer: 'Viewer' };
const ROLE_COLORS = {
  owner:  { bg: '#EEF2FF', color: '#4338CA', border: '#C7D2FE' },
  editor: { bg: '#FFF7ED', color: '#9A3412', border: '#FED7AA' },
  viewer: { bg: '#F0FDF4', color: '#166534', border: '#BBF7D0' },
};

function RolePill({ role }) {
  const s = ROLE_COLORS[role] || ROLE_COLORS.viewer;
  return (
    <span style={{
      display: 'inline-block', padding: '1px 7px', borderRadius: 999,
      fontSize: '10px', fontWeight: 600, letterSpacing: '0.03em',
      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
    }}>
      {ROLE_LABELS[role] || role}
    </span>
  );
}

function formatDate(s) {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d) ? '—' : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function StatusBadge({ status }) {
  const cls = { indexed: 'indexed', indexing: 'indexing', pending: 'pending', failed: 'failed' }[status] || 'pending';
  return <span className={`status-badge status-${cls}`}>{status || 'pending'}</span>;
}

// ── Share / Member Panel ───────────────────────────────────────────────────────
function SharePanel({ kbId, onClose }) {
  const [members,     setMembers]     = useState([]);
  const [loading,     setLoading]     = useState(true);
  const [inviteUser,  setInviteUser]  = useState('');
  const [inviteRole,  setInviteRole]  = useState('viewer');
  const [error,       setError]       = useState('');
  const [submitting,  setSubmitting]  = useState(false);

  const loadMembers = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await listKBMembers(kbId);
      setMembers(data || []);
    } catch { /* silent */ }
    setLoading(false);
  }, [kbId]);

  useEffect(() => { loadMembers(); }, [loadMembers]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteUser.trim()) return;
    setSubmitting(true); setError('');
    try {
      await addKBMember(kbId, inviteUser.trim(), inviteRole);
      setInviteUser('');
      await loadMembers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to invite user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await updateKBMember(kbId, userId, role);
      await loadMembers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update role');
    }
  };

  const handleRemove = async (userId) => {
    if (!confirm('Remove this member?')) return;
    try {
      await removeKBMember(kbId, userId);
      await loadMembers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to remove member');
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}
    onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div style={{
        background: 'var(--color-surface)', borderRadius: 'var(--radius)',
        border: '1px solid var(--color-border)', width: 460, maxWidth: '95vw',
        boxShadow: '0 8px 32px rgba(0,0,0,0.18)', overflow: 'hidden',
      }}>
        {/* Header */}
        <div style={{
          padding: 'var(--space-4) var(--space-5)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
            Manage Access
          </span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', lineHeight: 1 }}>
            ✕
          </button>
        </div>

        <div style={{ padding: 'var(--space-4) var(--space-5)' }}>
          {error && (
            <div style={{
              color: 'var(--color-error-text)', background: 'var(--color-error-bg)',
              padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-sm)',
              marginBottom: 'var(--space-3)', border: '1px solid var(--color-error)',
              fontSize: 'var(--text-xs)'
            }}>
              {error}
            </div>
          )}

          {/* Invite form */}
          <form onSubmit={handleInvite} style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
            <input
              type="text" placeholder="Username" value={inviteUser}
              onChange={e => setInviteUser(e.target.value)}
              style={{
                flex: 1, padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)',
                border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
                background: 'var(--color-bg)', color: 'var(--color-text)',
              }}
            />
            <select
              value={inviteRole} onChange={e => setInviteRole(e.target.value)}
              style={{
                padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)',
                border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
                background: 'var(--color-bg)', color: 'var(--color-text)',
              }}
            >
              <option value="viewer">Viewer</option>
              <option value="editor">Editor</option>
              <option value="owner">Owner</option>
            </select>
            <button
              type="submit" disabled={submitting}
              style={{
                padding: 'var(--space-2) var(--space-4)', fontSize: 'var(--text-sm)',
                background: 'var(--color-primary)', color: '#fff', border: 'none',
                borderRadius: 'var(--radius-sm)', cursor: submitting ? 'not-allowed' : 'pointer',
                fontWeight: 500,
              }}
            >
              {submitting ? '…' : 'Invite'}
            </button>
          </form>

          {/* Members list */}
          {loading ? (
            <div style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)', padding: 'var(--space-4)' }}>
              Loading…
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
              {members.map(m => (
                <div key={m.user_id} style={{
                  display: 'flex', alignItems: 'center', gap: 'var(--space-3)',
                  padding: 'var(--space-2) var(--space-3)',
                  background: 'var(--color-bg)', borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                }}>
                  <span style={{ flex: 1, fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--color-text)' }}>
                    {m.username}
                  </span>
                  <select
                    value={m.role}
                    onChange={e => handleRoleChange(m.user_id, e.target.value)}
                    style={{
                      padding: '2px 6px', fontSize: '12px',
                      border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)',
                      background: 'var(--color-surface)', color: 'var(--color-text)',
                    }}
                  >
                    <option value="viewer">Viewer</option>
                    <option value="editor">Editor</option>
                    <option value="owner">Owner</option>
                  </select>
                  <button
                    onClick={() => handleRemove(m.user_id)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--color-text-muted)', fontSize: 14, lineHeight: 1, padding: 2,
                    }}
                    title="Remove member"
                  >
                    ✕
                  </button>
                </div>
              ))}
              {members.length === 0 && (
                <div style={{ color: 'var(--color-text-faint)', fontSize: 'var(--text-sm)', textAlign: 'center', padding: 'var(--space-3)' }}>
                  No members yet.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export function KnowledgeBasePage() {
  // Use the shared hook — data comes from the module-level cache instantly
  const { knowledgeBases, refresh: refreshKBs } = useDocuments();

  const [selectedKB,     setSelectedKB]     = useState(null);
  const [documents,      setDocuments]      = useState([]);
  const [newKBName,      setNewKBName]      = useState('');
  const [newKBDesc,      setNewKBDesc]      = useState('');
  const [showNewKB,      setShowNewKB]      = useState(false);
  const [uploading,      setUploading]      = useState(false);
  const [uploadPercent,  setUploadPercent]  = useState(0);
  const [error,          setError]          = useState('');
  const [shareKBId,      setShareKBId]      = useState(null);  // which KB's share modal is open

  const handleCreateKB = async (e) => {
    e.preventDefault();
    if (!newKBName.trim()) return;
    try {
      await createKnowledgeBase(newKBName, newKBDesc);
      setNewKBName(''); setNewKBDesc(''); setShowNewKB(false);
      refreshKBs();
    } catch { /* silent */ }
  };

  const handleDeleteKB = async (kbId) => {
    if (!confirm('Delete this knowledge base? All documents inside will be lost.')) return;
    try {
      await deleteKnowledgeBase(kbId);
      if (selectedKB === kbId) { setSelectedKB(null); setDocuments([]); }
      refreshKBs();
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
      refreshKBs();
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
  // caller's role for the selected KB
  const myRole = selectedKBObj?.user_role || 'viewer';
  const canUpload = myRole === 'owner' || myRole === 'editor';
  const canDeleteDoc = myRole === 'owner' || myRole === 'editor';

  return (
    <div className="kb-layout">
      {/* Share modal */}
      {shareKBId && <SharePanel kbId={shareKBId} onClose={() => setShareKBId(null)} />}

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
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 4 }}>
                <div className="thread-title" style={{ minWidth: 0, flex: 1 }}>{kb.name}</div>
                <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0 }}>
                  {/* Share button — owners only */}
                  {(kb.user_role === 'owner') && (
                    <button
                      className="kb-del-btn"
                      title="Manage access"
                      onClick={e => { e.stopPropagation(); setShareKBId(kb.id); }}
                      style={{ fontSize: 12 }}
                    >
                      👥
                    </button>
                  )}
                  {/* Delete button — owners only */}
                  {(kb.user_role === 'owner') && (
                    <button
                      className="kb-del-btn"
                      onClick={e => { e.stopPropagation(); handleDeleteKB(kb.id); }}
                    >×</button>
                  )}
                </div>
              </div>
              <div className="thread-meta" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <span>{kb.document_count || 0} documents</span>
                {kb.user_role && <RolePill role={kb.user_role} />}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — documents */}
      <div className="kb-content">
        {selectedKB ? (
          <>
            <div className="kb-page-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <h2>{selectedKBObj?.name}</h2>
                {myRole && <RolePill role={myRole} />}
              </div>
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

            {/* Upload area — only for editors/owners */}
            {canUpload && (
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
            )}

            <div>
              <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: 'var(--space-3)' }}>
                Documents
                <span style={{ marginLeft: 8, fontSize: 'var(--text-xs)', fontWeight: 500, color: 'var(--color-text-faint)' }}>
                  {documents.length}
                </span>
              </h3>

              {documents.length === 0 && (
                <div style={{ textAlign: 'center', padding: 'var(--space-12)', color: 'var(--color-text-faint)', fontSize: 'var(--text-sm)' }}>
                  {canUpload ? 'No documents yet. Drop a file above to get started.' : 'No documents in this knowledge base.'}
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
                  {canDeleteDoc && (
                    <button className="doc-del-btn" onClick={() => handleDeleteDoc(doc.id)}>×</button>
                  )}
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
