import { useLocation, useNavigate } from 'react-router-dom';

const routes: Record<string, string> = {
  Overview: '/home',
  Research: '/discover',
  Queue: '/discover/queue',
  Library: '/content',
  Publishing: '/calendar',
  Activity: '/activity',
  Operations: '/settings',
  Profile: '/settings/profile',
  ResearchSettings: '/settings/research',
  Create: '/create',
};

export function useStudioRouting() {
  const location = useLocation();
  const navigate = useNavigate();
  const match = /^\/content\/([0-9a-f-]+)(?:\/carousel)?$/i.exec(location.pathname);
  const project = /^\/studio-content\/([0-9a-f-]+)$/i.exec(location.pathname);
  const setup = /^\/create(?:\/([0-9a-f-]+)\/(?:configure|review))?$/i.exec(location.pathname);
  const aliases: Record<string, string> = {
    '/': 'Overview',
    '/overview': 'Overview',
    '/library': 'Library',
  };
  const tab = project
    ? 'ContentWorkspace'
    : setup
      ? 'Create'
      : match
        ? 'Library'
        : Object.keys(routes).find((key) => routes[key] === location.pathname) ||
          aliases[location.pathname] ||
          'Not found';
  return {
    tab,
    id: match?.[1] || null,
    contentId: project?.[1] || null,
    setupId: setup?.[1] || null,
    navigateWorkspace: (name: string) => navigate(routes[name] || '/not-found'),
    openPost: (id: string) => navigate(`/content/${encodeURIComponent(id)}/carousel`),
  };
}
