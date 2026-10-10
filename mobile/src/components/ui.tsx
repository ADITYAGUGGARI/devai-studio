import { useState, type ReactNode } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  RefreshControl,
  StyleSheet,
  Keyboard,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const palette = {
  bg: '#F2EDE5',
  card: '#FAF7F2',
  border: '#82786B',
  text: '#20352D',
  muted: '#615E57',
  accent: '#173D32',
  warning: '#966000',
};
export function Button({
  title,
  onPress,
  disabled = false,
  secondary = false,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  secondary?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={title}
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        secondary && styles.secondaryButton,
        disabled && { opacity: 0.4 },
        pressed && { opacity: 0.75 },
      ]}
    >
      <Text style={[styles.buttonText, secondary && { color: palette.text }]}>{title}</Text>
    </Pressable>
  );
}
export function Field({
  label,
  value,
  onChange,
  multiline = false,
  secure = false,
  oneTimeCode = false,
  disabled = false,
  keyboardType,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  multiline?: boolean;
  secure?: boolean;
  oneTimeCode?: boolean;
  disabled?: boolean;
  keyboardType?: 'default' | 'decimal-pad' | 'number-pad';
}) {
  return (
    <View style={styles.field}>
      <Text style={styles.muted}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        accessibilityState={{ disabled }}
        editable={!disabled}
        testID={`field-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
        value={value}
        onChangeText={onChange}
        multiline={multiline}
        secureTextEntry={secure}
        returnKeyType={multiline ? 'default' : 'done'}
        onSubmitEditing={multiline ? undefined : Keyboard.dismiss}
        keyboardType={oneTimeCode ? 'number-pad' : keyboardType || 'default'}
        textContentType={oneTimeCode ? 'oneTimeCode' : secure ? 'password' : undefined}
        maxLength={oneTimeCode ? 6 : undefined}
        autoCapitalize="none"
        placeholderTextColor={palette.muted}
        style={[styles.input, multiline && { minHeight: 120, textAlignVertical: 'top' }]}
      />
    </View>
  );
}
export function Screen({
  title,
  subtitle,
  children,
  onRefresh,
  footer,
  compactTitle = false,
  safeTop = false,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  onRefresh?: () => Promise<void>;
  footer?: ReactNode;
  compactTitle?: boolean;
  safeTop?: boolean;
}) {
  const [refreshing, setRefreshing] = useState(false);
  return (
    <SafeAreaView
      style={{ flex: 1, backgroundColor: palette.bg }}
      edges={safeTop ? ['top', 'left', 'right', 'bottom'] : ['left', 'right', 'bottom']}
    >
      <ScrollView
        contentContainerStyle={styles.screen}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        refreshControl={
          onRefresh ? (
            <RefreshControl
              tintColor={palette.accent}
              refreshing={refreshing}
              onRefresh={() => {
                setRefreshing(true);
                void onRefresh().finally(() => setRefreshing(false));
              }}
            />
          ) : undefined
        }
      >
        <Text
          accessibilityRole="header"
          accessibilityLabel={title}
          numberOfLines={compactTitle ? 2 : undefined}
          style={[styles.title, compactTitle && { fontSize: 22, lineHeight: 28 }]}
        >
          {title}
        </Text>
        {subtitle && <Text style={styles.muted}>{subtitle}</Text>}
        {children}
      </ScrollView>
      {footer && <View style={styles.footer}>{footer}</View>}
    </SafeAreaView>
  );
}
export function Card({ children }: { children: ReactNode }) {
  return <View style={styles.card}>{children}</View>;
}
export function ErrorText({ value }: { value: string }) {
  return value ? (
    <Text accessibilityRole="alert" style={styles.warning}>
      {value}
    </Text>
  ) : null;
}
export function Segments<T extends string>({
  items,
  value,
  onChange,
}: {
  items: readonly T[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <View style={styles.segments}>
      {items.map((item) => (
        <Pressable
          key={item}
          accessibilityRole="tab"
          accessibilityLabel={item}
          accessibilityState={{ selected: value === item }}
          onPress={() => onChange(item)}
          style={[styles.segment, value === item && styles.segmentActive]}
        >
          <Text style={[styles.segmentText, value === item && { color: palette.bg }]}>{item}</Text>
        </Pressable>
      ))}
    </View>
  );
}
export const styles = StyleSheet.create({
  screen: { padding: 22, gap: 18, paddingBottom: 36, backgroundColor: palette.bg },
  title: { fontSize: 34, fontFamily: 'Georgia', fontWeight: '400', color: palette.text },
  heading: { fontSize: 19, fontWeight: '700', color: palette.text, lineHeight: 26 },
  text: { color: palette.text, fontSize: 17, lineHeight: 24, flexShrink: 1 },
  muted: { color: palette.muted, fontSize: 15, lineHeight: 22 },
  warning: { color: palette.warning, fontSize: 14, lineHeight: 21 },
  card: {
    padding: 18,
    gap: 12,
    borderRadius: 18,
    backgroundColor: palette.card,
    borderWidth: 1,
    borderColor: palette.border,
  },
  input: {
    padding: 14,
    color: palette.text,
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 12,
    backgroundColor: palette.bg,
    fontSize: 16,
  },
  field: { gap: 6 },
  button: {
    paddingHorizontal: 18,
    paddingVertical: 15,
    backgroundColor: palette.accent,
    borderRadius: 14,
    minHeight: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: { color: palette.bg, fontSize: 17, fontWeight: '700' },
  secondaryButton: { backgroundColor: palette.card, borderWidth: 1, borderColor: palette.border },
  row: { flexDirection: 'row', gap: 10, alignItems: 'center', flexWrap: 'wrap' },
  artwork: { width: '100%', aspectRatio: 0.8, borderRadius: 16, backgroundColor: palette.card },
  footer: {
    padding: 18,
    borderTopWidth: 1,
    borderTopColor: palette.border,
    backgroundColor: palette.bg,
    gap: 8,
  },
  segments: {
    flexDirection: 'row',
    backgroundColor: palette.card,
    borderRadius: 14,
    padding: 4,
    gap: 2,
  },
  segment: {
    flex: 1,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 10,
  },
  segmentActive: { backgroundColor: palette.accent },
  segmentText: { color: palette.muted, fontWeight: '600', fontSize: 12 },
});
