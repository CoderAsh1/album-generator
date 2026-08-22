/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: {
          50: '#fbf8ee',
          100: '#f5edd3',
          200: '#ebdaa8',
          300: '#dec076',
          400: '#d2a64c',
          500: '#c58e31',
          600: '#aa7127',
          700: '#885322',
          800: '#714221',
          900: '#5f371f',
        },
        navy: {
          850: '#0f172a',
          900: '#0b1120',
          950: '#060a12',
        }
      },
      fontFamily: {
        serif: ['"Playfair Display"', 'Georgia', 'serif'],
        cinzel: ['"Cinzel"', 'serif'],
        script: ['"Great Vibes"', 'cursive'],
        cormorant: ['"Cormorant Garamond"', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
