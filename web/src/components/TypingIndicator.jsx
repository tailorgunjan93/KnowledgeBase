import React from 'react';

const TypingIndicator = () => {
  return (
    <div className="typing-indicator" style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-1)',
      padding: 'var(--space-2) var(--space-4)',
      background: 'var(--color-surface-alt)',
      borderRadius: 'var(--radius-md)',
      width: 'fit-content',
      margin: 'var(--space-2) 0'
    }}>
      <div className="dot" style={{ width: 6, height: 6, background: 'var(--color-text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out' }}></div>
      <div className="dot" style={{ width: 6, height: 6, background: 'var(--color-text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out 0.2s' }}></div>
      <div className="dot" style={{ width: 6, height: 6, background: 'var(--color-text-muted)', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out 0.4s' }}></div>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: scale(0); }
          40% { transform: scale(1.0); }
        }
      `}</style>
    </div>
  );
};

export default TypingIndicator;
