import type { Advisory, HealthProfile } from '../types/api';
/** Deliberately simple DEMO logic. The reviewed backend rule engine owns production advice. */
export function makeDemoAdvisory(aqi: number, profile: HealthProfile | null): Advisory {
  const reasons: Advisory['reasons'] = [{ key: 'reasonAqi', values: { aqi } }];
  let sensitivity = 0;
  if (profile?.ageGroup === 'child') {
    sensitivity += 1;
    reasons.push({ key: 'reasonChild' });
  }
  if (profile?.ageGroup === 'older') {
    sensitivity += 1;
    reasons.push({ key: 'reasonOlder' });
  }
  for (const condition of profile?.conditions ?? []) {
    sensitivity += 1;
    reasons.push({ key: `reason_${condition}` });
  }
  if (profile?.activityLevel === 'high') {
    sensitivity += 1;
    reasons.push({ key: 'reasonActivity' });
  }
  const score = (aqi > 150 ? 2 : aqi > 100 ? 1 : 0) + (sensitivity > 0 ? 1 : 0) + (sensitivity > 1 && aqi > 50 ? 1 : 0);
  const level = score >= 2 ? 'high' : score === 1 ? 'elevated' : 'low';
  if (!profile)
    reasons.push({ key: 'reasonGeneric' });
  return { level, recommendationKey: `recommend_${level}`, reasons, aqi, personalized: !!profile, isDemo: true };
}
