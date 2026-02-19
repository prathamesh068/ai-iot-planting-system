/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  corePlugins: {
    preflight: false, // Disable CSS reset to avoid conflicts with antd
  },
  theme: {
    extend: {},
  },
  plugins: [],
};
