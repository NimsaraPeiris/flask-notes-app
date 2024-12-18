/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html", // points templates
  ],
  theme: {
    extend: {
      colors :{
            /* CSS HEX */
        'tea-green': '#c6ebbeff',
        'celadon': '#a9dbb8ff',
        'air-blue': '#7ca5b8ff',
        'egyptian-blue': '#38369aff',
        'phthalo-blue': '#020887ff'
      },
    },
  },
  plugins: [],
}

