import { useState, useEffect, useCallback } from 'react';
import { listUsers, updateUserRole, getAdminStats } from '../api/adminApi';

const ROLE_COLORS = {
  admin: { bg: '#EEF2FF', color: '#4338CA', border: '#C7D2FE' },
  user:  { bg: '#F0FDF4', color: '#166534', border: '#BBF7D0' },
};

function RolePill({ role }) {
  const s = ROLE_COLORS[role] || ROLE_COLORS.user;
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 8px',
      borderRadius: '999px',
      fontSize: '11px',
      fontWeight: 600,
      letterSpacing: '0.02em',
      background: s.bg,
      color: s.color,
      border: `1px solid ${s.border}`,
    }}>
      {role}
    </span>
  );
}

function StatCard({ label, value }) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)',
      padding: 'var(--space-4) var(--space-5)',
      flex: 1,
      minWidth: 120,
    }}>
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, color: 'var(--color-text)' }}>{value ?? '—'}</div>
    </div>
  );
}

export function AdminPage() {
  const [users,   setUsers]   = useState([]);
  const [stats,   setStats]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState('');
  const [updating, setUpdating] = useState(null); // user_id being updated

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [usersRes, statsRes] = await Promise.all([listUsers(), getAdminStats()]);
      setUsers(usersRes.data.items || []);
      setStats(statsRes.data);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleRoleToggle = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    setUpdating(userId);
    try {
      await updateUserRole(userId, newRole);
      setUsers(prev => prev.map(u => u.user_id === userId ? { ...u, role: newRole } : u));
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to update role');
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--color-text)', marginBottom: 4 }}>
          Admin Panel
        </h1>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
          Manage users and system settings
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', flexWrap: 'wrap' }}>
          <StatCard label="Total Users"      value={stats.total_users}     />
          <StatCard label="Knowledge Bases"  value={stats.total_kbs}       />
          <StatCard label="Documents"        value={stats.total_documents} />
        </div>
      )}

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

      {/* Users table */}
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}>
        <div style={{
          padding: 'var(--space-4) var(--space-5)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
            Users ({users.length})
          </span>
          <button
            style={{
              fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)',
              background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px',
              borderRadius: 'var(--radius-sm)',
            }}
            onClick={load}
          >
            ↺ Refresh
          </button>
        </div>

        {loading ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>
            Loading…
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['#', 'Username', 'Email', 'Role', 'Joined', 'Action'].map(h => (
                  <th key={h} style={{
                    padding: 'var(--space-3) var(--space-4)',
                    textAlign: 'left',
                    fontSize: '11px',
                    fontWeight: 600,
                    color: 'var(--color-text-muted)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {users.map((u, i) => (
                <tr
                  key={u.user_id}
                  style={{
                    borderBottom: i < users.length - 1 ? '1px solid var(--color-border)' : 'none',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--color-surface-hover, rgba(0,0,0,0.02))'}
                  onMouseLeave={e => e.currentTarget.style.background = ''}
                >
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)' }}>
                    {u.user_id}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--color-text)' }}>
                    {u.username}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                    {u.email || '—'}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <RolePill role={u.role} />
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <button
                      disabled={updating === u.user_id}
                      onClick={() => handleRoleToggle(u.user_id, u.role)}
                      style={{
                        fontSize: '12px',
                        padding: '4px 10px',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--color-border)',
                        background: 'var(--color-bg)',
                        color: u.role === 'admin' ? '#DC2626' : '#2563EB',
                        cursor: updating === u.user_id ? 'not-allowed' : 'pointer',
                        opacity: updating === u.user_id ? 0.6 : 1,
                        fontWeight: 500,
                      }}
                    >
                      {updating === u.user_id ? '…' : u.role === 'admin' ? 'Demote' : 'Promote'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
