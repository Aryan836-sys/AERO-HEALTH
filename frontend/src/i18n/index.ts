import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './en.json';
import ne from './ne.json';
let language = 'en';
try {
  language = localStorage.getItem('aero-language') === 'ne' ? 'ne' : 'en';
}
catch { /* Private browsing may disable storage. */ }
void i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, ne: { translation: ne } },
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
