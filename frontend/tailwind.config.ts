import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bookworm: {
          50: "#f2fbf4",
          100: "#dff6e7",
          500: "#2e8b57",
          700: "#216b43",
          900: "#153a2b",
        },
      },
    },
  },
  plugins: [],
};

export default config;
