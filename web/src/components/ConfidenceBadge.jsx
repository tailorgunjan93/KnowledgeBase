import React from 'react';

const ConfidenceBadge = ({ score }) => {
  if (!score && score !== 0) return null;
  
  // Handle string score if needed
  const numScore = typeof score === 'string' ? parseFloat(score) : score;
  
  const color =
    numScore >= 0.7 ? 'var(--color-success)' :
    numScore >= 0.5 ? 'var(--color-warning)' :
    'var(--color-error)';

  return (
    <span style={{
      background: color,
      color: '#fff',
      borderRadius: 'var(--radius-sm)',
      padding: '2px 8px',
      fontSize: 'var(--text-xs)',
      fontWeight: 600,
      marginLeft: 'var(--space-2)',
      display: 'inline-block',
      verticalAlign: 'middle'
    }}>
      {Math.round(numScore * 100)}% confidence
    </span>
  );
};

export default ConfidenceBadge;
