#!/usr/bin/env node
/**
 * Example: load all sources and show a coverage summary.
 *
 * Run from the repo root:
 *    npm install yaml
 *    node examples/load_sources.js
 */

import { readdir, readFile } from 'fs/promises';
import { parse } from 'yaml';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SOURCES_DIR = join(__dirname, '..', 'sources');

async function loadAllSources() {
  const files = await readdir(SOURCES_DIR);
  const yamlFiles = files
    .filter(f => f.endsWith('.yml') && !f.startsWith('_'))
    .sort();

  return Promise.all(
    yamlFiles.map(async f => parse(await readFile(join(SOURCES_DIR, f), 'utf8')))
  );
}

async function main() {
  const sources = await loadAllSources();
  const active = sources.filter(s => s.kitsuno_status === 'active');
  const wishlist = sources.filter(s => s.kitsuno_status === 'wishlist');
  const inactive = sources.filter(s => s.kitsuno_status === 'inactive');

  console.log(`=== Total: ${sources.length} sources ===`);
  console.log(`  active:   ${active.length}`);
  console.log(`  wishlist: ${wishlist.length}`);
  console.log(`  inactive: ${inactive.length}`);

  console.log('\n=== Active sources by focus ===');
  const focusCounts = {};
  for (const s of active) focusCounts[s.focus] = (focusCounts[s.focus] || 0) + 1;
  for (const [focus, n] of Object.entries(focusCounts).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${focus.padEnd(12)} ${n}`);
  }

  console.log('\n=== Country coverage (active only) ===');
  const countryToSources = {};
  for (const s of active) {
    for (const c of s.countries) {
      if (!countryToSources[c]) countryToSources[c] = [];
      countryToSources[c].push(s.slug);
    }
  }
  for (const country of Object.keys(countryToSources).sort()) {
    const slugs = countryToSources[country];
    const preview = slugs.slice(0, 4).join(', ') + (slugs.length > 4 ? '...' : '');
    console.log(`  ${country}: ${slugs.length} sources — ${preview}`);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
