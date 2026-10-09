import { useQuery } from '@tanstack/react-query';
import { request } from '../../services/api';
export function VersionHistory({
  id,
  version,
  locked,
  onAction,
}: {
  id: string;
  version: string;
  locked: boolean;
  onAction: (op: () => Promise<unknown>) => Promise<void>;
}) {
  const { data = [] } = useQuery({
    queryKey: ['versions', id, version],
    queryFn: () =>
      request<
        {
          id: string | null;
          version: string;
          reason: string;
          created_at: string;
          snapshot: { title: string; caption: string };
        }[]
      >(`/posts/${id}/versions`),
  });
  return (
    <details className="panel">
      <summary>Version history</summary>
      {data.map((row) => (
        <div className="source-evidence" key={row.version}>
          <strong>
            Version {row.version} · {row.reason}
          </strong>
          <p>{row.snapshot.title}</p>
          <p>{row.snapshot.caption}</p>
          {row.id && row.version !== version && (
            <button
              className="secondary"
              disabled={locked}
              onClick={() =>
                onAction(() => request(`/posts/${id}/versions/${row.id}/restore`, 'POST'))
              }
            >
              Restore version {row.version} as draft
            </button>
          )}
        </div>
      ))}
    </details>
  );
}
