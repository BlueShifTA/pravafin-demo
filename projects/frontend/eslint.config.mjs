import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const config = [
  {
    ignores: [".next/**", "out/**", "dist/**", "coverage/**", "src/lib/generated/**"],
  },
  ...compat.extends("next/core-web-vitals", "prettier"),
  {
    files: ["src/**/*.{js,jsx,ts,tsx}"],
    rules: {
      "import/first": "error",
      "no-restricted-imports": [
        "error",
        {
          patterns: ["./*", "../*"],
        },
      ],
    },
  },
  {
    files: ["src/app/layout.tsx"],
    rules: {
      "import/first": "error",
      "no-restricted-imports": [
        "error",
        {
          patterns: ["./*", "!./globals.css", "../*"],
        },
      ],
    },
  },
];

export default config;
