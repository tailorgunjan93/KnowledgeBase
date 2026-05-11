import React, { useState, useRef } from 'react';

const DropZone = ({ onFiles, disabled }) => {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    if (!disabled) setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (!disabled && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFiles([...e.dataTransfer.files]);
    }
  };

  const handleClick = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFiles([...e.target.files]);
      e.target.value = '';
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      style={{
        border: `2px dashed ${dragging ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-8)',
        textAlign: 'center',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all var(--transition-fast)',
        background: dragging ? 'var(--color-primary-light)' : 'var(--color-surface-alt)',
        opacity: disabled ? 0.6 : 1,
        color: dragging ? 'var(--color-primary-dark)' : 'var(--color-text-muted)'
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.doc,.docx,.txt,.md,.xlsx,.xls"
        style={{ display: 'none' }}
        onChange={handleInputChange}
        disabled={disabled}
      />
      <div style={{ marginBottom: 'var(--space-2)' }}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <p style={{ fontSize: 'var(--text-base)', fontWeight: 500, margin: 0 }}>
        {dragging ? 'Drop files here' : 'Drop files here or click to browse'}
      </p>
      <p style={{ fontSize: 'var(--text-xs)', marginTop: 'var(--space-2)' }}>
        Supports PDF, TXT, MD, DOCX
      </p>
    </div>
  );
};

export default DropZone;
