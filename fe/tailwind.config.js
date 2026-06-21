/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Tín có thể định nghĩa màu Teal riêng cho dự án NCKH ở đây
        stuTeal: '#008080', 
      }
    },
  },
  plugins: [],
}