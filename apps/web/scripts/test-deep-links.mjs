import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const expectedFallback = '/* /index.html 200'
const publicFallback = (await readFile(new URL('../public/_redirects', import.meta.url), 'utf8')).trim()
const builtFallback = (await readFile(new URL('../dist/_redirects', import.meta.url), 'utf8')).trim()
const builtIndex = await readFile(new URL('../dist/index.html', import.meta.url), 'utf8')

assert.equal(publicFallback, expectedFallback, 'public fallback must serve index.html for every deep link')
assert.equal(builtFallback, expectedFallback, 'build artifact must preserve the deep-link fallback')
assert.match(builtIndex, /<div id="root"><\/div>/, 'build artifact must contain the SPA mount point')

console.log('deep-link fallback verified in public/ and dist/')
