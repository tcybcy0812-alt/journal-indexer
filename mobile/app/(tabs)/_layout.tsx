import { NativeTabs } from 'expo-router/unstable-native-tabs';

export default function TabLayout() {
  return (
    <NativeTabs
      iconColor={{
        default: '#9CA3AF',
        selected: '#2563EB',
      }}
    >
      <NativeTabs.Trigger name="index" labelVisibilityMode="labeled">
        <NativeTabs.Trigger.Icon sf="magnifyingglass" />
        <NativeTabs.Trigger.Label>爬取</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>

      <NativeTabs.Trigger name="history" labelVisibilityMode="labeled">
        <NativeTabs.Trigger.Icon sf="clock.arrow.trianglehead.counterclockwise.rotate.90" />
        <NativeTabs.Trigger.Label>历史</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
