import js from '@eslint/js';
import tseslint from 'typescript-eslint';
export default tseslint.config(
  { ignores: ['dist/**'] },
  { files: ['**/*.ts', '**/*.tsx'], extends: [js.configs.recommended, ...tseslint.configs.strictTypeChecked], languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } }, rules: { '@typescript-eslint/consistent-type-assertions': ['error', { assertionStyle: 'never' }] } }
);
