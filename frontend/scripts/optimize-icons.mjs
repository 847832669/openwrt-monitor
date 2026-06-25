import { readdir, readFile, writeFile } from 'node:fs/promises'
import { optimize } from 'svgo'

const root = new URL('../src/assets/', import.meta.url)
const dirs = ['brands', 'lan-icons']

const config = {
  multipass: true,
  plugins: [
    {
      name: 'preset-default',
      params: {
        overrides: {
          cleanupIds: false,
        },
      },
    },
    'removeDimensions',
    'sortAttrs',
  ],
}

let totalBefore = 0
let totalAfter = 0

for (const dir of dirs) {
  const files = await readdir(new URL(`${dir}/`, root), { withFileTypes: true })
    .catch(() => [])

  for (const entry of files) {
    if (!entry.isFile() || !entry.name.endsWith('.svg')) continue
    const fileUrl = new URL(`${dir}/${entry.name}`, root)
    const input = await readFile(fileUrl, 'utf8')
    const result = optimize(input, { ...config, path: fileUrl.pathname })
    if (result.error) throw new Error(`${entry.name}: ${result.error}`)

    totalBefore += Buffer.byteLength(input)
    totalAfter += Buffer.byteLength(result.data)
    await writeFile(fileUrl, `${result.data.trim()}\n`)
  }
}

const saved = totalBefore - totalAfter
const pct = totalBefore ? (saved / totalBefore * 100).toFixed(1) : '0.0'
console.log(`Optimized SVG icons: ${(totalBefore / 1024).toFixed(1)} KB -> ${(totalAfter / 1024).toFixed(1)} KB (${pct}% saved)`)
