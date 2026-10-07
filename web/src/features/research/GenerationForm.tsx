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
      <h2>Generate a source-backed AI carousel</h2>
      <p className="hint">
        Paste a verified article excerpt. All generated content requires fact-checking and approval.
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
      <label htmlFor="source-excerpt">Source excerpt (at least 120 characters)</label>
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
          busy || !title.trim() || !url.startsWith('https://') || excerpt.trim().length < 120
        }
      >
        ✳ Generate 8-slide draft
      </button>
    </form>
  );
}
