import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1f2933",
        meadow: "#3a7d44",
        butter: "#f6c453",
        berry: "#c44569",
        sky: "#5aa9e6",
        paper: "#fffdf7",
      },
      boxShadow: {
        soft: "0 16px 40px rgba(31, 41, 51, 0.12)",
      },
    },
  },
  plugins: [],
};

export default config;
