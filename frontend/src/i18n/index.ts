import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import ne from './ne.json';
import enLive from './en.live.json';
// Same switch as services/api.ts (kept separate so this file doesn't pull in the API layer).
const demo = import.meta.env.VITE_USE_MOCK_API !== 'false';
// Demo wording ("fictional", "sample") is wrong once real data is showing, so
// live mode overrides those strings. Nepali strings for overridden keys are
// dropped rather than left saying "demo": they fall back to the English live
// wording until a Nepali translation of en.live.json is added.
const english: Record<string, string> = demo ? en : { ...en, ...enLive };
const nepali: Record<string, string> = demo
  ? ne
  : Object.fromEntries(Object.entries(ne).filter(([key]) => !(key in enLive)));
let language = 'en';
try {
  language = localStorage.getItem('aero-language') === 'ne' ? 'ne' : 'en';
}
catch { /* Private browsing may disable storage. */ }
void i18n.use(initReactI18next).init({
  resources: { en: { translation: english }, ne: { translation: nepali } },
  lng: language, fallbackLng: 'en', supportedLngs: ['en', 'ne'],
  keySeparator: false, interpolation: { escapeValue: false },
});
i18n.on('languageChanged', (lang) => {
  document.documentElement.lang = lang;
  try {
    localStorage.setItem('aero-language', lang);
  }
  catch { /* Language still changes for this session. */ }
});
document.documentElement.lang = language;
export default i18n;
