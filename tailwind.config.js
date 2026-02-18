/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        loopymart: {
          blue: '#2874f0',
          'blue-dark': '#1a5dc7',
          yellow: '#ffe500',
          orange: '#ff9f00',
          green: '#388e3c',
          gray: '#f1f3f6',
          'gray-dark': '#e0e0e0',
        },
        text: {
          primary: '#212121',
          secondary: '#878787',
          hint: '#b0b0b0',
        }
      },
      fontFamily: {
        sans: ['Roboto', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Oxygen', 'Ubuntu', 'Cantarell', 'sans-serif'],
      },
      boxShadow: {
        'card': '0 1px 2px 0 rgba(0,0,0,.2)',
        'card-hover': '0 2px 8px 0 rgba(0,0,0,.15)',
        'header': '0 1px 1px 0 rgba(0,0,0,.16)',
        'dropdown': '0 4px 16px 0 rgba(0,0,0,.2)',
      },
      borderRadius: {
        'sm': '2px',
      },
      maxWidth: {
        'container': '1280px',
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      }
    },
  },
  plugins: [],
}
