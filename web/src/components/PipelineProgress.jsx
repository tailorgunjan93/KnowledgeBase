/* PipelineProgress — step-by-step RAG retrieval visualization
   Maps backend status strings to numbered steps with progress bars.
   Modes: kb_advanced | kb_simple | web | general
*/

const PIPELINES = {
  kb_advanced: [
    { label: 'Searching knowledge base', statusKey: '🔍 Searching knowledge base...' },
    { label: 'Optimizing query',         statusKey: '🧠 Optimizing search query...' },
    { label: 'Precision retrieval',      statusKey: '🎯 Retrieving precision sources...' },
    { label: 'Generating response',      statusKey: 'Synthesizing answer...' },
  ],
  kb_simple: [
    { label: 'Searching knowledge base', statusKey: '🔍 Searching knowledge base...' },
    { label: 'Generating response',      statusKey: 'Synthesizing answer...' },
  ],
  web: [
    { label: 'Searching the web',   statusKey: '🌐 Searching the web...' },
    { label: 'Generating response', statusKey: 'Synthesizing answer...' },
  ],
  general: [
    { label: 'Processing query',    statusKey: '🧠 Thinking...' },
    { label: 'Generating response', statusKey: 'Synthesizing answer...' },
  ],
};

export function PipelineProgress({ currentStatus, seenStatuses, mode }) {
  const steps = PIPELINES[mode] || PIPELINES.general;

  // Index of the currently active step (-1 if status doesn't match any known step)
  const activeIdx = steps.findIndex(s => s.statusKey === currentStatus);

  const getState = (idx) => {
    // Step has been seen before and isn't the active one → done
    if (seenStatuses.has(steps[idx].statusKey) && steps[idx].statusKey !== currentStatus) {
      return 'done';
    }
    if (activeIdx >= 0) {
      if (idx < activeIdx) return 'done';
      if (idx === activeIdx) return 'active';
    }
    return 'pending';
  };

  const LABELS = { done: 'Done ✓', active: '...', pending: '' };

  return (
    <div className="pipeline-card">
      <div className="pipeline-header">
        <div className="pipeline-header-pulse" />
        Processing
      </div>

      <div className="pipeline-steps">
        {steps.map((step, idx) => {
          const state = getState(idx);
          return (
            <div key={idx} className="pipeline-step">
              {/* Step number / checkmark */}
              <div className={`pipeline-step-num ${state}`}>
                {state === 'done' ? '✓' : idx + 1}
              </div>

              {/* Label + progress bar */}
              <div className="pipeline-step-body">
                <div className={`pipeline-step-label ${state}`}>{step.label}</div>
                <div className="pipeline-bar-track">
                  <div className={`pipeline-bar-fill ${state}`} />
                </div>
              </div>

              {/* Status tag */}
              <div className={`pipeline-step-tag ${state}`}>
                {LABELS[state]}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
