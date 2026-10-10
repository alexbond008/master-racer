// Save/load. Fiat 126 is permanent (can't be wagered or lost).
const KEY = 'masterracer.save.v1';
const fresh = () => ({ owned: ['fiat126'], carId: 'fiat126', cash: 1500, mods: {}, raceIdx: 0, finished: false });

export function loadSave() {
  try {
    if (location.search.includes('reset')) localStorage.removeItem(KEY);
    const s = JSON.parse(localStorage.getItem(KEY));
    if (s && Array.isArray(s.owned) && s.owned.length) return { ...fresh(), ...s };
  } catch { /* private mode etc. */ }
  return fresh();
}
export function saveGame(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* ignore */ } }
