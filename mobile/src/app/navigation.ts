import type { NavigatorScreenParams } from '@react-navigation/native';
export type WorkspaceTabs = {
  Today: undefined;
  Research: undefined;
  Library: undefined;
  Activity: undefined;
  Settings: undefined;
};
export type Routes = {
  Workspace: NavigatorScreenParams<WorkspaceTabs> | undefined;
  Review: { id: string };
  Topic: { id: string };
  Search: undefined;
  Queue: undefined;
  AddSource: undefined;
  Activity: undefined;
  Operations: undefined;
  Publishing: undefined;
  Profile: undefined;
};
