/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: { ink: '#18312e', mint: '#13b992', violet: '#6550df', canvas: '#f5f7f6' },
      fontFamily: { sans: ['Manrope', 'Noto Sans Devanagari', 'system-ui', 'sans-serif'] },
      borderRadius: { panel: '24px' },
    },
  },
  plugins: [],
};
