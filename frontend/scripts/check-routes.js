// 路由有效性校验脚本（临时工具）
const fs = require('fs'), path = require('path')
const pagesJson = JSON.parse(fs.readFileSync('pages.json', 'utf8'))
const registered = new Set(pagesJson.pages.map(p => '/' + p.path))
pagesJson.tabBar.list.forEach(t => registered.add('/' + t.pagePath))

function walk(d) {
  let r = []
  if (!fs.existsSync(d)) return r
  for (const f of fs.readdirSync(d)) {
    const p = path.join(d, f)
    const s = fs.statSync(p)
    if (s.isDirectory() && !['node_modules', 'unpackage', '_cli_backup', 'admin', '.hbuilderx'].includes(f)) r = r.concat(walk(p))
    else if (f.endsWith('.vue') || f.endsWith('.js')) r.push(p)
  }
  return r
}

const files = walk('pages').concat(walk('components'), walk('common'), ['App.vue', 'main.js'])
const urlRe = /(?:navigateTo|redirectTo|reLaunch|switchTab)\s*\(\s*\{\s*url:\s*['"]([^'"]+)['"]/g
let bad = 0
for (const f of files) {
  const src = fs.readFileSync(f, 'utf8')
  let m
  while ((m = urlRe.exec(src))) {
    const u = m[1].split('?')[0]
    if (!u.startsWith('/')) continue
    if (!registered.has(u)) { console.log('BAD:', f, '->', m[1]); bad++ }
  }
}
console.log(bad === 0 ? 'ALL ROUTES OK' : 'FOUND ' + bad + ' BAD')
