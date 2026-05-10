const ConfidenceBadge = ({ score }) => {
  if (score == null) return null;
  const n   = typeof score === 'string' ? parseFloat(score) : score;
  const cls = n >= 0.7 ? 'high' : n >= 0.5 ? 'mid' : 'low';
  return (
    <span className={`confidence-badge confidence-${cls}`}>
      {Math.round(n * 100)}% confidence
    </span>
  );
};

export default ConfidenceBadge;
