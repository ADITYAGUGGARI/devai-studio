import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  KeyboardAvoidingView,
  Modal,
  Platform,
  ScrollView,
  Switch,
  Text,
  View,
} from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';
import { useNavigation, usePreventRemove, type NavigationProp } from '@react-navigation/native';
import type { Routes } from '../app/navigation';
import { ApiError, request } from '../services/api';
import { Button, Card, ErrorText, Field, Screen, styles, palette } from '../components/ui';
import {
  researchCategories,
  schedulePayload,
  type ResearchSchedule,
} from '../../../shared/researchSchedule';

export function ResearchSettings() {
  const navigation = useNavigation<NavigationProp<Routes>>();
  const [saved, setSaved] = useState<ResearchSchedule | null>(null);
  const [draft, setDraft] = useState<ResearchSchedule | null>(null);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Loading research settings…');
  const [busy, setBusy] = useState(false);
  const [conflict, setConflict] = useState<ResearchSchedule | null>(null);
  const [zonePicker, setZonePicker] = useState(false);
  const [timePicker, setTimePicker] = useState(false);
  const [zoneQuery, setZoneQuery] = useState('');
  const [zones, setZones] = useState<string[]>([]);
  const [zoneError, setZoneError] = useState('');
  const key = useRef('');
  const runKey = useRef('');
  const dirty = Boolean(
    saved &&
    draft &&
    JSON.stringify(schedulePayload(saved)) !== JSON.stringify(schedulePayload(draft)),
  );
  async function load() {
    try {
      const account = await request<{ workspace_id: string }>('/auth/me');
      const value = await request<ResearchSchedule>(
        `/v1/workspaces/${account.workspace_id}/settings`,
      );
      setSaved(value);
      setDraft(value);
      setError('');
      setStatus('Saved');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load research settings');
      setStatus('');
    }
  }
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    if (!zonePicker) return;
    let active = true;
    const timer = setTimeout(() => {
      setZoneError('');
      void request<{ items: string[] }>(`/v1/time-zones?q=${encodeURIComponent(zoneQuery)}`).then(
        (result) => {
          if (active) setZones(result.items);
        },
        (cause) => {
          if (active)
            setZoneError(cause instanceof Error ? cause.message : 'Timezone search failed');
        },
      );
    }, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [zonePicker, zoneQuery]);
  function edit(next: ResearchSchedule) {
    key.current = '';
    setDraft(next);
  }
  async function save() {
    if (!draft || !draft.canEdit || conflict) return false;
    key.current ||= `ios-schedule-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setBusy(true);
    setError('');
    setStatus('Saving…');
    try {
      const value = await request<ResearchSchedule>(
        `/v1/workspaces/${draft.workspaceId}/settings`,
        'PATCH',
        schedulePayload(draft),
        { 'Idempotency-Key': key.current },
      );
      setSaved(value);
      setDraft(value);
      key.current = '';
      setStatus('Saved');
      return true;
    } catch (cause) {
      if (cause instanceof ApiError) {
        key.current = '';
        if (
          cause.status === 409 &&
          typeof cause.detail === 'object' &&
          cause.detail &&
          'server' in cause.detail
        )
          setConflict(cause.detail.server as ResearchSchedule);
      }
      setError(cause instanceof Error ? cause.message : 'Save failed');
      setStatus('Save failed · changes retained');
      return false;
    } finally {
      setBusy(false);
    }
  }
  usePreventRemove(dirty, ({ data }) => {
    Alert.alert('Keep your changes?', 'Your research schedule has unsaved changes.', [
      { text: 'Stay', style: 'cancel' },
      {
        text: 'Discard local changes',
        style: 'destructive',
        onPress: () => navigation.dispatch(data.action),
      },
      {
        text: 'Save and leave',
        onPress: () => {
          void save().then((success) => {
            if (success) navigation.dispatch(data.action);
          });
        },
      },
    ]);
  });
  async function runNow() {
    if (!saved || dirty || !saved.canRunResearch) return;
    runKey.current ||= `ios-research-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setBusy(true);
    setError('');
    try {
      await request(
        '/v1/research/runs',
        'POST',
        { categoryIds: saved.categories },
        { 'Idempotency-Key': runKey.current },
      );
      runKey.current = '';
      navigation.navigate('Activity');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not start research');
      if (cause instanceof ApiError) runKey.current = '';
    } finally {
      setBusy(false);
    }
  }
  const disabled = busy || !draft?.canEdit;
  const hours = Number(draft?.researchLocalTime.split(':')[0] || 8);
  const minutes = Number(draft?.researchLocalTime.split(':')[1] || 0);
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <Screen
        title="Daily discovery"
        compactTitle
        footer={
          draft ? (
            <View>
              <ErrorText value={error} />
              <Text style={styles.muted} accessibilityLiveRegion="polite">
                {dirty && !busy ? 'Unsaved changes' : status}
              </Text>
              <Button
                title={busy ? 'Saving…' : 'Save schedule'}
                disabled={disabled || !dirty || !draft.categories.length || Boolean(conflict)}
                onPress={() => void save()}
              />
            </View>
          ) : undefined
        }
      >
        {!draft && (
          <>
            <ErrorText value={error} />
            <Text style={styles.muted}>{status}</Text>
          </>
        )}
        {!draft ? (
          <Button title="Retry settings" onPress={() => void load()} />
        ) : (
          <>
            <Card>
              <Text style={styles.heading}>Daily research</Text>
              <Text style={styles.text}>
                Collect the previous 24 hours and keep ranked findings for review.
              </Text>
              <Switch
                accessibilityLabel="Enable daily research"
                value={draft.researchEnabled}
                disabled={disabled}
                onValueChange={(value) => edit({ ...draft, researchEnabled: value })}
              />
              <Button
                secondary
                title={`Research time · ${draft.researchLocalTime}`}
                disabled={disabled}
                onPress={() => setTimePicker(true)}
              />
              <Button
                secondary
                title={`Timezone · ${draft.timeZone}`}
                disabled={disabled}
                onPress={() => setZonePicker(true)}
              />
            </Card>
            <Card>
              <Text style={styles.heading}>Category mix</Text>
              {researchCategories.map((category) => (
                <View
                  key={category}
                  style={{
                    flexDirection: 'row',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    minHeight: 48,
                  }}
                >
                  <Text style={styles.text}>{category}</Text>
                  <Switch
                    accessibilityLabel={`Include ${category}`}
                    disabled={disabled}
                    value={draft.categories.includes(category)}
                    onValueChange={(value) =>
                      edit({
                        ...draft,
                        categories: value
                          ? [...draft.categories, category]
                          : draft.categories.filter((item) => item !== category),
                      })
                    }
                  />
                </View>
              ))}
            </Card>
            <Text style={styles.muted}>
              Automatic drafts are unavailable while the revised generation workflow is being built.
              This schedule never publishes content.
            </Text>
            <Text style={styles.text}>
              {saved?.nextRunAt
                ? `Next saved run: ${new Date(saved.nextRunAt).toLocaleString(undefined, { timeZone: saved.timeZone })} (${saved.timeZone})`
                : 'Daily research is off. Manual research remains available in Discover.'}
            </Text>
            {!draft.canEdit && (
              <Text style={styles.muted}>Only a studio owner can edit this schedule.</Text>
            )}
            {saved?.workerHealth && !saved.workerHealth.healthy && (
              <Text style={styles.muted}>
                The worker is offline. Research jobs stay queued until it reconnects.
              </Text>
            )}
            <Button
              secondary
              title="Run research now"
              disabled={busy || dirty || !saved?.canRunResearch}
              onPress={() => void runNow()}
            />
            {conflict && (
              <Card>
                <Text style={styles.heading}>Schedule changed on another device</Text>
                <Button
                  title="Keep my changes"
                  onPress={() => {
                    edit({ ...draft, revision: conflict.revision });
                    setSaved({ ...draft, ...conflict });
                    setConflict(null);
                    setError('');
                  }}
                />
                <Button
                  secondary
                  title="Use saved schedule"
                  onPress={() => {
                    const value = { ...draft, ...conflict };
                    setSaved(value);
                    setDraft(value);
                    setConflict(null);
                    setError('');
                  }}
                />
              </Card>
            )}
          </>
        )}
        <Modal
          visible={timePicker}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setTimePicker(false)}
        >
          <View style={{ flex: 1, padding: 24, backgroundColor: palette.bg }}>
            <Text style={styles.heading}>Choose research time</Text>
            <DateTimePicker
              value={new Date(2020, 0, 1, hours, minutes)}
              mode="time"
              display="spinner"
              textColor={palette.text}
              onChange={(_, value) => {
                if (value && draft)
                  edit({
                    ...draft,
                    researchLocalTime: `${String(value.getHours()).padStart(2, '0')}:${String(value.getMinutes()).padStart(2, '0')}`,
                  });
              }}
            />
            <Text style={styles.muted}>
              This changes your draft. Save the schedule to apply it.
            </Text>
            <Button title="Done" onPress={() => setTimePicker(false)} />
          </View>
        </Modal>
        <Modal
          visible={zonePicker}
          animationType="slide"
          presentationStyle="pageSheet"
          onRequestClose={() => setZonePicker(false)}
        >
          <View style={{ flex: 1, padding: 24, backgroundColor: palette.bg }}>
            <Text style={styles.heading}>Choose timezone</Text>
            <Field label="Search timezones" value={zoneQuery} onChange={setZoneQuery} />
            <ErrorText value={zoneError} />
            <ScrollView keyboardShouldPersistTaps="handled">
              {zones.map((zone) => (
                <Button
                  key={zone}
                  secondary
                  title={zone}
                  onPress={() => {
                    if (draft) edit({ ...draft, timeZone: zone });
                    setZonePicker(false);
                  }}
                />
              ))}
            </ScrollView>
            <Button title="Done" onPress={() => setZonePicker(false)} />
          </View>
        </Modal>
      </Screen>
    </KeyboardAvoidingView>
  );
}
