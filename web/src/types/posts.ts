export type PostStatus =
  'draft' | 'pending_review' | 'approved' | 'rejected' | 'publishing' | 'published';
export type ReviewAction = 'submit' | 'approve' | 'reject';

export interface Slide {
  id: string;
  headline: string;
  body: string;
  position: number;
  visual_direction?: string | null;
  has_artwork?: boolean;
  composition_mode?: string;
  artwork_current?: boolean;
  validation?: ImageValidation | null;
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
  verification?: { supported: boolean; issues: string[]; human_review_required: boolean } | null;
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
    created_topic_ids?: string[];
    skipped_urls?: string[];
    warnings?: string[];
  } | null;
  error: string | null;
}

export interface DailyRunSummary {
  mode?: 'research' | 'carousel';
  topic: string;
  timezone: string;
  run: DailyRun | null;
  latest_research?: Job | null;
}

export interface SourceInput {
  title: string;
  url: string;
  excerpt: string;
}

export interface ImageValidation {
  image_sha256?: string;
  passed: boolean;
  issues: string[];
  human_review_required: boolean;
}

export interface Job {
  id: string;
  kind: string;
  status:
    | 'queued'
    | 'running'
    | 'retry_wait'
    | 'completed'
    | 'completed_with_warnings'
    | 'failed'
    | 'needs_reconciliation';
  step: string;
  progress: number;
  total: number;
  attempts: number;
  max_attempts: number;
  available_at: string;
  created_at: string;
  finished_at: string | null;
  error: string | null;
  payload: { post_id?: string; topic_id?: string; slide_id?: string; version?: string };
  result: {
    post_id?: string;
    warnings?: string[];
    created_topic_ids?: string[];
    skipped_urls?: string[];
    instagram_media_id?: string;
  } | null;
}

export interface Topic {
  selected?: boolean;
  id: string;
  title: string;
  url: string;
  source: string;
  excerpt: string;
  category: string;
  priority: number;
  status: 'queued' | 'generating' | 'used' | 'archived';
  verification: 'unverified' | 'primary_source' | 'human_verified';
  published_at: string | null;
  retrieved_at: string;
  post_id: string | null;
  error: string | null;
}

export interface WorkflowConfig {
  worker_enabled: boolean;
  daily_enabled: boolean;
  daily_hour: number;
  timezone: string;
  openai_configured: boolean;
  instagram_configured: boolean;
  public_media_configured: boolean;
}
