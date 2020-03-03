
export function getCurrentZoneData(state) {
  const { grid } = state.data;
  const zoneName = state.application.selectedZoneName;
  const i = state.application.selectedZoneTimeIndex;
  if (!grid || !zoneName) {
    return null;
  }
  if (i == null) {
    return grid.zones[zoneName];
  }
  return (state.data.histories[zoneName] || {})[i];
}
