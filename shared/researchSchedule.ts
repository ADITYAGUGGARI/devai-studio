/** Shared persisted schedule contract used by web and native clients. */
export interface ResearchSchedule {
  workspaceId: string;
  revision: number;
  researchEnabled: boolean;
  researchLocalTime: string;
  timeZone: string;
  categories: string[];
  autoDraftOptions: { enabled: boolean };
  nextRunAt: string | null;
  canEdit: boolean;
  autoDraftAvailable: boolean;
  canRunResearch: boolean;
  workerHealth?: { healthy: boolean; last_seen: string | null };
}

export const researchCategories = ['news', 'tutorial', 'architecture', 'tools', 'insight'];

export function schedulePayload(value: ResearchSchedule) {
  return {
    expectedRevision: value.revision,
    researchEnabled: value.researchEnabled,
    researchLocalTime: value.researchLocalTime,
    timeZone: value.timeZone,
    categories: value.categories,
    autoDraftOptions: value.autoDraftOptions,
  };
}
