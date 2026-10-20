/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        google: {
          blue: '#1a73e8',
          blueHover: '#1557d0',
          blueLight: '#e8f0fe',
          blueBorder: '#dadce0',
          green: '#1e8e3e',
          greenLight: '#e6f4ea',
          greenBorder: '#ceead6',
          red: '#d93025',
          redLight: '#fce8e6',
          redBorder: '#fad2cf',
          yellow: '#f9ab00',
          amber: '#e37400',
          amberLight: '#fef7e0',
          amberBorder: '#feefc3',
          gray: '#5f6368',
          dark: '#202124',
          subtle: '#3c4043',
          border: '#dadce0',
          bg: '#f8fafd',
          surface: '#ffffff',
        },
      },
      fontFamily: {
        sans: ['"Google Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['"Roboto Mono"', 'ui-monospace', 'Menlo', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15)',
        'card-hover': '0 1px 3px 0 rgba(60,64,67,.3), 0 4px 8px 3px rgba(60,64,67,.15)',
        'dialog': '0 8px 24px -4px rgba(60,64,67,.3), 0 4px 8px -2px rgba(60,64,67,.15)',
        'panel': '0 1px 3px 0 rgba(0, 0, 0, 0.08), 0 1px 2px -1px rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      }
    },
  },
  plugins: [],
}
