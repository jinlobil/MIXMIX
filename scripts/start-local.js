const {spawn} = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const python = process.platform === 'win32' ? 'python' : 'python3';
const children = [
  spawn(python, ['backend/server.py'], {cwd: root, stdio: 'inherit'}),
  spawn(process.execPath, ['frontend/server.js'], {cwd: root, stdio: 'inherit'})
];
let stopping = false;
function stop(code = 0) { if (stopping) return; stopping = true; children.forEach(child => child.kill()); setTimeout(() => process.exit(code), 100); }
children.forEach(child => child.on('exit', code => { if (!stopping && code) stop(code); }));
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
