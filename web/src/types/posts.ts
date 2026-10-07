export type PostStatus =
  'draft' | 'pending_review' | 'approved' | 'rejected' | 'publishing' | 'published';
export type ReviewAction = 'submit' | 'approve' | 'reject';

export interface Slide {
  id: string;
  headline: string;
  body: string;
  position: number;
}

export interface Post {
  id: string;
  title: string;
  caption: string;
  status: PostStatus;
  version: string;
  created: string;
  slides: Slide[];
  evidence: ArticleEvidence | null;
}

export interface ArticleEvidence {
  source_title: string;
  source_name: string;
  source_url: string;
  published_at: string | null;
  retrieved_at: string;
  topic: string;
  editorial_angle: string;
  excerpt: string;
}

export interface DailyRun {
  id: string;
  local_date: string;
  timezone: string;
  status: 'running' | 'completed' | 'completed_with_warnings' | 'failed';
  attempt_count: number;
  started_at: string;
  finished_at: string | null;
  retry_after: string | null;
  result: {
    post_id?: string;
    topic?: string;
    source_title?: string;
    source_url?: string;
    editorial_angle?: string;
    slide_count?: number;
    warnings?: string[];
  } | null;
  error: string | null;
}

export interface DailyRunSummary {
  topic: string;
  timezone: string;
  run: DailyRun | null;
}

export interface SourceInput {
  title: string;
  url: string;
  excerpt: string;
}
