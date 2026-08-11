const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');

const HOST = process.env.FRONTEND_HOST || '127.0.0.1';
const PORT = Number(process.env.FRONTEND_PORT) || 4173;
const API_HOST = process.env.BACKEND_HOST || '127.0.0.1';
const API_PORT = Number(process.env.BACKEND_PORT) || 8000;
const ROOT = __dirname;
const TYPES = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'};

function proxy(req, res) {
  const upstream = http.request({hostname: API_HOST, port: API_PORT, path: req.url, method: req.method, headers: {...req.headers, host: `${API_HOST}:${API_PORT}`}}, response => {
    res.writeHead(response.statusCode, response.headers);
    response.pipe(res);
  });
  upstream.on('error', () => {
    res.writeHead(502, {'Content-Type':'application/json; charset=utf-8'});
    res.end(JSON.stringify({error:'Python 백엔드에 연결할 수 없습니다.'}));
  });
  req.pipe(upstream);
}

const server = http.createServer(async (req, res) => {
  const pathname = new URL(req.url, `http://${req.headers.host || 'localhost'}`).pathname;
  if (pathname.startsWith('/api/') || pathname.startsWith('/uploads/')) return proxy(req, res);
  try {
    const relative = pathname === '/' ? 'index.html' : decodeURIComponent(pathname).replace(/^\/+/, '');
    const file = path.resolve(ROOT, relative);
    if (!file.startsWith(`${ROOT}${path.sep}`)) throw Object.assign(new Error(), {code:'FORBIDDEN'});
    const content = await fs.readFile(file);
    res.writeHead(200, {'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream', 'Cache-Control':'no-store, max-age=0'});
    res.end(content);
  } catch (error) {
    res.writeHead(error.code === 'FORBIDDEN' ? 403 : 404, {'Content-Type':'text/plain; charset=utf-8'});
    res.end(error.code === 'FORBIDDEN' ? 'Forbidden' : 'Not found');
  }
});

server.listen(PORT, HOST, () => console.log(`Prompt Atelier Node 프론트엔드 → http://${HOST}:${PORT}`));
