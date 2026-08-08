import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

const files = [
  'app-config.ts',
  'components/app/welcome-view.tsx',
  'components/app/view-controller.tsx',
  'components/agents-ui/blocks/agent-session-view-01/components/agent-session-block.tsx',
  'hooks/useAgentErrors.tsx',
];

const source = files.map((file) => readFileSync(join(root, file), 'utf8')).join('\n');

const requiredPhrases = [
  'Suraksha Saathi',
  'Telugu',
  'UPI fraud',
  'Ready',
  'Connecting',
  'Listening',
  'Speaking',
  'Call ended',
  'Start again',
  'Microphone permission blocked',
  'browser site settings',
  'data-day3-state',
  'data-day3-speaker',
];

const missing = requiredPhrases.filter((phrase) => !source.includes(phrase));

if (missing.length > 0) {
  console.error(`Day 3 frontend contract missing: ${missing.join(', ')}`);
  process.exit(1);
}

console.log('Day 3 frontend contract verified.');
