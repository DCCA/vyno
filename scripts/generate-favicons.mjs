#!/usr/bin/env node
/**
 * Generate PNG favicon variants from the SVG source.
 * Usage: node scripts/generate-favicons.mjs [source]
 *   source defaults to web/public/favicon.svg
 *
 * Outputs:
 *   web/public/favicon-16.png   (16×16)
 *   web/public/favicon-32.png   (32×32)
 *   web/public/apple-touch-icon.png (180×180)
 */

import { readFileSync } from "node:fs"
import { createRequire } from "node:module"
import { resolve, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, "..")

async function main() {
  let sharp
  try {
    // sharp is installed under web/node_modules
    const require = createRequire(resolve(root, "web/package.json"))
    sharp = require("sharp")
  } catch {
    console.error("sharp is required. Install it first:\n  npm --prefix web install -D sharp")
    process.exit(1)
  }

  const src = resolve(root, process.argv[2] || "web/public/favicon.svg")
  const outDir = resolve(root, "web/public")
  const svgBuf = readFileSync(src)

  const sizes = [
    { name: "favicon-16.png", size: 16 },
    { name: "favicon-32.png", size: 32 },
    { name: "apple-touch-icon.png", size: 180 },
  ]

  for (const { name, size } of sizes) {
    await sharp(svgBuf)
      .resize(size, size)
      .png()
      .toFile(resolve(outDir, name))
    console.log(`  ✓ ${name} (${size}×${size})`)
  }

  console.log("\nDone. PNG favicons written to web/public/")
}

main()
