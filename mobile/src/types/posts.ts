export interface Post {
  id: string;
  title: string;
  caption: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'publishing' | 'published';
  version: string;
  slides: { id: string; headline: string; body: string }[];
}
