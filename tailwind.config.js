/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './blueprints/**/templates/**/*.html',
    './frontend/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        link: '#4caf50',
        'link-hover': '#45a049',
      },
    },
  },
  plugins: [],
};
