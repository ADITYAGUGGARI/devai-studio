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
}

export interface SourceInput {
  title: string;
  url: string;
  excerpt: string;
}
