import type { ReactNode } from 'react';
import type { Account } from '../app/state';
const entries = [
  ['Overview', 'Today', '⌂'],
  ['Research', 'Research', '⌕'],
  ['Library', 'Library', '▤'],
  ['Publishing', 'Publishing', '↗'],
  ['Activity', 'Activity', '◷'],
  ['Operations', 'Settings', '⚙'],
] as const;
export function WorkspaceShell({
  tab,
  onNavigate,
  account,
  onLogout,
  activeCount,
  children,
}: {
  tab: string;
  onNavigate: (tab: string) => void;
  account: Account | null;
  onLogout: () => void;
  activeCount: number;
  children: ReactNode;
}) {
  const active = (id: string) =>
    tab === id ||
    (id === 'Operations' && ['Profile', 'ResearchSettings'].includes(tab)) ||
    (id === 'Research' && tab === 'Queue');
  return (
    <div className="shell desktop-studio">
      <aside className="studio-sidebar">
        <div className="brand">
          <span className="brandmark">✳</span>
          <span>
            devai studio<small>DEVELOPER CONTENT</small>
          </span>
        </div>
        <nav aria-label="Main navigation">
          {entries.slice(0, 4).map(([id, label, icon]) => (
            <button
              key={id}
              aria-current={active(id) ? 'page' : undefined}
              className={active(id) ? 'nav active' : 'nav'}
              onClick={() => onNavigate(id)}
            >
              <span aria-hidden="true" className="nav-icon">
                {icon}
              </span>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <nav aria-label="Workspace tools">
            {entries.slice(4).map(([id, label, icon]) => (
              <button
                key={id}
                aria-current={active(id) ? 'page' : undefined}
                className={active(id) ? 'nav active' : 'nav'}
                onClick={() => onNavigate(id)}
              >
                <span aria-hidden="true" className="nav-icon">
                  {icon}
                </span>
                {label}
                {id === 'Activity' && activeCount > 0 && (
                  <span className="count-badge">{activeCount}</span>
                )}
              </button>
            ))}
          </nav>
          <div className="workspace-note">
            Private workspace
            <br />
            <span>Human approval before publishing</span>
          </div>
        </div>
      </aside>
      <main>
        <header className="studio-topbar">
          <span>
            Studio <span className="breadcrumb-separator">/</span>{' '}
            <strong>
              {tab === 'ResearchSettings'
                ? 'Research schedule'
                : entries.find((e) => e[0] === tab)?.[1] || tab}
            </strong>
          </span>
          <div className="account-strip">
            <span className="account-avatar" aria-hidden="true">
              {account?.email.slice(0, 1).toUpperCase()}
            </span>
            <span className="account-label">
              {account?.email}
              <small>{account?.role}</small>
            </span>
            <button className="ghost" onClick={onLogout}>
              Sign out
            </button>
          </div>
        </header>
        <nav className="mobile-nav" aria-label="Workspace navigation">
          {entries.map(([id, label]) => (
            <button
              key={id}
              aria-current={active(id) ? 'page' : undefined}
              className={active(id) ? 'nav active' : 'nav'}
              onClick={() => onNavigate(id)}
            >
              {label}
            </button>
          ))}
        </nav>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
