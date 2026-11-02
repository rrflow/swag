import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve, sep, extname } from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execute = promisify(execFile);
const port = Number(process.env.SWAG_UI_PORT ?? 8891);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid SWAG_UI_PORT');
const allowedHosts = new Set([`127.0.0.1:${port}`, `localhost:${port}`]);
const statusScript = fileURLToPath(new URL('../../tools/swag_dev_status.py', import.meta.url));
let pendingStatus;
const root = fileURLToPath(new URL('../dist/', import.meta.url));
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json' };
createServer(async (request, response) => {
  if (!allowedHosts.has(request.headers.host) ||
      (request.headers.origin && request.headers.origin !== `http://${request.headers.host}`)) {
    response.writeHead(403); response.end('Origin rejected'); return;
  }
  if (request.method !== 'GET') { response.writeHead(405); response.end('Read-only interface'); return; }
  try {
    const pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (pathname === '/api/dev/status') {
      try {
        pendingStatus ??= execute(process.env.SWAG_PYTHON ?? 'python', [statusScript],
          { timeout: 30000, maxBuffer: 2_000_000, windowsHide: true }).finally(() => { pendingStatus = undefined; });
        const { stdout } = await pendingStatus;
        const data = JSON.parse(stdout);
        if (data.schema !== 'swag.dev-status/v1') throw new Error('Invalid read model');
        response.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' });
        response.end(JSON.stringify(data));
      } catch {
        response.writeHead(503, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
        response.end(JSON.stringify({ error: 'Developer status unavailable; inspect local traces.' }));
      }
      return;
    }
    const path = resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    if (!path.startsWith(root.endsWith(sep) ? root : root + sep)) throw new Error('outside root');
    const body = await readFile(path);
    response.writeHead(200, {
      'Content-Type': types[extname(path)] ?? 'application/octet-stream',
      'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
      'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    });
    response.end(body);
  } catch {
    response.writeHead(404); response.end('Not found');
  }
}).listen(port, '127.0.0.1', () => console.log(`SWAG developer UI: http://127.0.0.1:${port}/dev.html`));
