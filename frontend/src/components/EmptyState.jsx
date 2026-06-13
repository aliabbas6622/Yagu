import { InboxIcon } from 'lucide-react';

export default function EmptyState({ title = 'Nothing here yet', description = '' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center gap-3">
      <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
           style={{ background: 'rgba(148,163,184,0.08)' }}>
        <InboxIcon className="w-6 h-6" style={{ color: 'var(--text-muted)' }} />
      </div>
      <p className="text-sm font-semibold" style={{ color: 'var(--text-secondary)' }}>{title}</p>
      {description && (
        <p className="text-xs max-w-xs" style={{ color: 'var(--text-muted)' }}>{description}</p>
      )}
    </div>
  );
}
