import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'

// Explicit rather than relying on @testing-library/react's auto-cleanup,
// which detects test-framework globals - not exposed here since
// `test.globals` isn't enabled in vite.config.ts (afterEach etc. are
// imported explicitly instead). Without this, DOM from one test leaks
// into the next, causing "multiple elements found" failures in later
// tests within the same file.
afterEach(() => {
  cleanup()
})
