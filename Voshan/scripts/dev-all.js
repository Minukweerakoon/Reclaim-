#!/usr/bin/env node

/**
 * Run Voshan Node backend + ML service together from one command.
 * Usage: npm run dev:all
 */

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const rootDir = path.resolve(__dirname, '..');
const mlDir = path.join(rootDir, 'ml-service');

const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const defaultVenvPython = path.resolve(rootDir, '..', '.venv', 'bin', 'python');
const pythonCmd = process.env.VOSHAN_PYTHON_BIN || (fs.existsSync(defaultVenvPython) ? defaultVenvPython : 'python3');

const children = [];
let shuttingDown = false;

function prefixStream(child, label) {
  if (child.stdout) {
    child.stdout.on('data', (chunk) => {
      const text = String(chunk);
      process.stdout.write(text.split('\n').filter(Boolean).map((line) => `[${label}] ${line}`).join('\n') + '\n');
    });
  }
  if (child.stderr) {
    child.stderr.on('data', (chunk) => {
      const text = String(chunk);
      process.stderr.write(text.split('\n').filter(Boolean).map((line) => `[${label}] ${line}`).join('\n') + '\n');
    });
  }
}

function shutdown(exitCode = 0) {
  if (shuttingDown) return;
  shuttingDown = true;

  for (const child of children) {
    if (!child.killed) {
      child.kill('SIGTERM');
    }
  }

  setTimeout(() => {
    for (const child of children) {
      if (!child.killed) child.kill('SIGKILL');
    }
    process.exit(exitCode);
  }, 1500);
}

if (!fs.existsSync(mlDir)) {
  console.error('[dev-all] Missing ml-service directory:', mlDir);
  process.exit(1);
}

console.log('[dev-all] Starting Voshan backend + ML service...');
console.log(`[dev-all] Python: ${pythonCmd}`);

const backend = spawn(npmCmd, ['run', 'dev'], {
  cwd: rootDir,
  env: { ...process.env },
  stdio: ['inherit', 'pipe', 'pipe'],
});
children.push(backend);
prefixStream(backend, 'backend');

const ml = spawn(pythonCmd, ['app.py'], {
  cwd: mlDir,
  env: { ...process.env },
  stdio: ['inherit', 'pipe', 'pipe'],
});
children.push(ml);
prefixStream(ml, 'ml');

backend.on('exit', (code, signal) => {
  if (!shuttingDown) {
    console.error(`[dev-all] Backend exited (code=${code}, signal=${signal}). Stopping all services.`);
    shutdown(code || 1);
  }
});

ml.on('exit', (code, signal) => {
  if (!shuttingDown) {
    console.error(`[dev-all] ML service exited (code=${code}, signal=${signal}). Stopping all services.`);
    shutdown(code || 1);
  }
});

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));
