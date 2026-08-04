const {spawn} = require('node:child_process');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const python = process.platform === 'win32' ? 'py' : 'python3';
const pythonArgs = process.platform === 'win32' ? ['-3', 'backend/server.py'] : ['backend/server.py'];
const children = [
  spawn(python, pythonArgs, {cwd: root, stdio: 'inherit'}),
  spawn(process.execPath, ['frontend/server.js'], {cwd: root, stdio: 'inherit'})
];
let stopping = false;
function stop(code = 0) { if (stopping) return; stopping = true; children.forEach(child => child.kill()); setTimeout(() => process.exit(code), 100); }
children.forEach(child => child.on('exit', code => { if (!stopping && code) stop(code); }));
process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());
