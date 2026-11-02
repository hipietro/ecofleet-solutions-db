/**
 * File overview
 * Purpose: Define static code checks for the frontend.
 * Responsibilities: Combine JavaScript, TypeScript, React Hooks and Fast Refresh rules while
 *   ignoring build output.
 * Connections: The package.json lint script reads this file; its rules cover application TS and
 *   TSX files.
 */

// --- Imports and cross-module dependencies ---
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

// --- Lint configuration: ignore generated output and apply the shared TypeScript/React rule sets. ---
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    // --- Browser environment: allow DOM globals used by fetch, storage and navigation. ---
    languageOptions: {
      globals: globals.browser,
    },
  },
])
