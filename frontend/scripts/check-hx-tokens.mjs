import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const tokensPath = path.join(__dirname, '../src/assets/styles/tokens.css')
const required = [
  '--hx-space-1', '--hx-space-2', '--hx-space-3', '--hx-space-4',
  '--hx-space-5', '--hx-space-6', '--hx-space-7',
  '--hx-color-primary', '--hx-color-bg-layout', '--hx-color-bg-container',
  '--hx-color-text-primary', '--hx-color-text-secondary',
  '--hx-radius-sm', '--hx-radius-md', '--hx-radius-lg',
  '--hx-shadow-sm', '--hx-shadow-md',
  '--hx-z-header', '--hx-z-dropdown', '--hx-z-drawer', '--hx-z-modal', '--hx-z-ai-float',
  '--copilot-spacing-sm', // alias 保活
]

if (!fs.existsSync(tokensPath)) {
  console.error('FAIL: tokens.css missing at', tokensPath)
  process.exit(1)
}
const css = fs.readFileSync(tokensPath, 'utf8')
const missing = required.filter((k) => !css.includes(k))
if (missing.length) {
  console.error('FAIL: missing tokens:', missing.join(', '))
  process.exit(1)
}
if (!css.includes('#1677ff')) {
  console.error('FAIL: primary #1677ff not found')
  process.exit(1)
}
console.log('PASS: hx tokens present')
