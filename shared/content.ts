export type OutputFormat = 'carousel' | 'reel';
export function studioRole(account: { role: string; workspace_role?: string } | null) {
  return account?.workspace_role || (account?.role === 'admin' ? 'owner' : account?.role);
}
export function canEditStudio(account: { role: string; workspace_role?: string } | null) {
  return ['owner', 'editor'].includes(studioRole(account) || '');
}
export function canReviewStudio(account: { role: string; workspace_role?: string } | null) {
  return ['owner', 'reviewer'].includes(studioRole(account) || '');
}
export interface ContentOptions {
  audience: string;
  tone: 'Clear' | 'Analytical' | 'Conversational' | 'Editorial';
  language: 'English';
  slideCount: number;
  durationSec: number;
  voiceId: 'coral' | 'marin' | 'cedar' | 'alloy' | 'nova' | 'sage' | null;
  subtitles: boolean;
}
export const defaultContentOptions: ContentOptions = {
  audience: 'Software engineers',
  tone: 'Clear',
  language: 'English',
  slideCount: 8,
  durationSec: 35,
  voiceId: 'coral',
  subtitles: true,
};
export interface Scene {
  id: string;
  headline: string;
  body: string;
  script: string;
  durationSec: number;
  visualDirection?: string;
  imageAssetId?: string;
  audioAssetId?: string;
  imageCurrent?: boolean;
  audioCurrent?: boolean;
  lastImageFailure?: string[];
}
export interface StudioJob {
  id: string;
  status: string;
  step: string;
  progress: number;
  total: number;
  error: string | null;
  cancel_requested: boolean;
}
export interface StudioDocument<T> {
  id: string;
  revision: number;
  state: string;
  updated_at: string;
  data: T;
}
export interface SetupData {
  topicId: string;
  formats: OutputFormat[];
  options: ContentOptions;
  contentId?: string;
}
export interface OutputData {
  format: OutputFormat;
  source: { id: string; title: string; url: string; excerpt: string; source: string };
  title?: string;
  caption: string;
  scenes: Scene[];
  voiceId: ContentOptions['voiceId'];
  subtitles: boolean;
  stage: string;
  postId?: string;
  renderId?: string;
  renderCurrent?: boolean;
  approvalCurrent?: boolean;
  grounding?: {
    supported: boolean;
    issues: string[];
    claims?: { claim: string; evidence_quote: string }[];
  };
  budgetRemaining: number;
  providerRequests?: number;
  revisionRequests?: { actorId: string; notes: string; revision: number }[];
  approval?: { id: string; assetHashes: Record<string, string> };
  renderValidation?: {
    duration_seconds: number;
    passed: boolean;
    decoded: boolean;
    audio_present: boolean;
  };
}
export type StudioOutput = StudioDocument<OutputData> & { job?: StudioJob };
export type StudioContent = StudioDocument<{
  title: string;
  topicId: string;
  source: OutputData['source'];
}> & { outputs: StudioOutput[] };
export function contentList(value: { items: StudioContent[] }): { items: StudioContent[] } {
  if (
    !Array.isArray(value?.items) ||
    value.items.some(
      (item) =>
        typeof item?.id !== 'string' ||
        typeof item?.data?.title !== 'string' ||
        !Array.isArray(item?.outputs) ||
        item.outputs.some(
          (output) =>
            typeof output?.state !== 'string' ||
            !['carousel', 'reel'].includes(output?.data?.format),
        ),
    )
  )
    throw new Error(
      'The content service returned an unreadable response. Retry to refresh saved projects.',
    );
  return value;
}
export interface ProviderCapabilities {
  revision: string;
  providerConfigured: boolean;
  providerLiveVerified: boolean;
  formats: Record<OutputFormat, { configured: boolean; issues: string[] }>;
  defaultBudgetPerOutput: number;
  budgetUnit: string;
  subtitlesSupported: boolean;
}
export function timelinePayload(output: StudioOutput) {
  return {
    expectedRevision: output.revision,
    caption: output.data.caption,
    voiceId: output.data.voiceId,
    subtitles: output.data.subtitles,
    scenes: output.data.scenes.map(({ id, headline, body, script, durationSec }) => ({
      id,
      headline,
      body,
      script,
      durationSec,
    })),
  };
}
