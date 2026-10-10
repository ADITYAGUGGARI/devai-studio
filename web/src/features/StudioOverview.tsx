import type { Post, Topic, Job } from '../types/posts';
export function StudioOverview({
  posts,
  topics,
  jobs,
  onOpen,
  onNavigate,
}: {
  posts: Post[];
  topics: Topic[];
  jobs: Job[];
  onOpen: (id: string) => void;
  onNavigate: (tab: string) => void;
}) {
  const next =
    posts.find((p) => p.status === 'pending_review') || posts.find((p) => p.status === 'draft');
  const active = jobs.filter((j) => ['queued', 'running', 'retry_wait'].includes(j.status)).length;
  return (
    <div className="studio-overview">
      <section className="panel next-step" aria-labelledby="next-step-heading">
        <div className="eyebrow">YOUR NEXT STEP</div>
        <h2 id="next-step-heading">
          {next
            ? 'Give your next story the final touch.'
            : 'A great carousel starts with a credible story.'}
        </h2>
        <p className="subtitle">
          {next?.title ||
            'Explore recent AI developments, review the evidence, and choose what to explain.'}
        </p>
        <button
          className="primary"
          onClick={() => (next ? onOpen(next.id) : onNavigate('Research'))}
        >
          {next ? 'Continue carousel' : 'Explore research'} →
        </button>
      </section>
      <div className="stats">
        <button className="stat stat-link" onClick={() => onNavigate('Research')}>
          <span>Stories in queue</span>
          <strong>{topics.filter((t) => t.status === 'queued').length}</strong>
        </button>
        <button className="stat stat-link" onClick={() => onNavigate('Library')}>
          <span>Needs review</span>
          <strong>{posts.filter((p) => p.status === 'pending_review').length}</strong>
        </button>
        <button className="stat stat-link" onClick={() => onNavigate('Publishing')}>
          <span>Approved to share</span>
          <strong>{posts.filter((p) => p.status === 'approved').length}</strong>
        </button>
      </div>
      {active > 0 && (
        <button className="activity-link secondary" onClick={() => onNavigate('Activity')}>
          {active} background {active === 1 ? 'task is' : 'tasks are'} running · View progress →
        </button>
      )}
      <div className="sectiontitle">
        <h2>Recent drafts</h2>
        <button className="ghost" onClick={() => onNavigate('Library')}>
          View all
        </button>
      </div>
      <div className="recent-drafts">
        {posts.slice(0, 3).map((p) => (
          <button className="panel recent-draft" key={p.id} onClick={() => onOpen(p.id)}>
            <span className={`pill ${p.status}`}>{p.status.replaceAll('_', ' ')}</span>
            <h3>{p.title}</h3>
            <span className="hint">
              {p.slides.length} slides · Version {p.version} →
            </span>
          </button>
        ))}
      </div>
      {!posts.length && (
        <p className="hint">
          Your first carousel will appear here after you choose and approve a topic.
        </p>
      )}
    </div>
  );
}
