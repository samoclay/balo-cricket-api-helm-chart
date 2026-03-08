// Commitlint configuration — https://commitlint.js.org/
// Enforces the Conventional Commits specification on every commit in a PR.
// See: https://www.conventionalcommits.org/
//
// Rules are validated by .github/workflows/commitlint.yml on every pull request.
//
// Using a .mjs config (ESM) so we can define the `ignores` predicate to
// gracefully skip bootstrap / initial-setup commits that pre-date this policy.
// Note: wagoid/commitlint-github-action@v6 requires .mjs, not .js.

/** @type {import('@commitlint/types').UserConfig} */
export default {
  extends: ['@commitlint/config-conventional'],

  // Skip validation for repo-bootstrap commits that pre-date this policy.
  // Covers "Initial commit", "Initial plan", "WIP" and similar setup messages.
  ignores: [
    (msg) => /^(Initial\b|WIP\b)/i.test(msg),
  ],

  rules: {
    // Allow the custom 'helm' type alongside the standard set
    'type-enum': [
      2, // error (not warn)
      'always',
      [
        'feat',     // ✨ new feature
        'fix',      // 🐛 bug fix
        'docs',     // 📚 documentation
        'helm',     // ⛵ helm chart changes
        'ci',       // 👷 CI/CD
        'chore',    // 🔧 maintenance
        'refactor', // ♻️  refactor
        'perf',     // ⚡ performance
        'test',     // 🧪 tests
        'style',    // 🎨 formatting
        'revert',   // ⏪ revert
      ],
    ],
    // Subject line should not end with a period
    'subject-full-stop': [2, 'never', '.'],
    // Subject line should start with lowercase
    'subject-case': [2, 'never', ['sentence-case', 'start-case', 'pascal-case', 'upper-case']],
  },
};
