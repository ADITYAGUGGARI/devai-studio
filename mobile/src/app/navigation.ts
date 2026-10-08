import type { NavigatorScreenParams } from '@react-navigation/native';
export type WorkspaceTabs = {
  Today: undefined;
  Research: undefined;
  Library: undefined;
  Publishing: undefined;
};
export type Routes = {
  Workspace: NavigatorScreenParams<WorkspaceTabs> | undefined;
  Review: { id: string };
  Topic: { id: string };
  Search: undefined;
  AddSource: undefined;
  Activity: undefined;
  Operations: undefined;
};
