import { useState } from 'react';
import type { SourceInput } from '../../types/posts';

interface Props {
  busy: boolean;
  onGenerate: (source: SourceInput) => Promise<void>;
}

export function GenerationForm({ busy, onGenerate }: Props) {
  const [title, setTitle] = useState('');
  const [url, setUrl] = useState('');
  const [excerpt, setExcerpt] = useState('');
  return (
    <form
      className="panel"
      onSubmit={(event) => {
        event.preventDefault();
        void onGenerate({ title, url, excerpt });
      }}
    >
      <h2>Add a source to the topic queue</h2>
      <p className="hint">
        Save a primary source excerpt, then review and verify its evidence in the queue before
        generating.
      </p>
      <label htmlFor="source-title">Story headline</label>
      <input
        id="source-title"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
        required
      />
      <label htmlFor="source-url">Primary source URL</label>
      <input
        id="source-url"
        type="url"
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        required
      />
      <label htmlFor="source-excerpt">Source excerpt (at least 240 characters)</label>
      <textarea
        id="source-excerpt"
        rows={4}
        value={excerpt}
        onChange={(event) => setExcerpt(event.target.value)}
        required
      />
      <button
        className="primary"
        disabled={
          busy || !title.trim() || !url.startsWith('https://') || excerpt.trim().length < 240
        }
      >
        Add source to queue
      </button>
    </form>
  );
}
