/**
 * Frees port 5000 before starting the dev server (runs as predev).
 * Prevents EADDRINUSE when a previous backend process is still running.
 */

const { execSync } = require('child_process');
const PORT = process.env.PORT || 5000;

function killPort(port) {
  const isWindows = process.platform === 'win32';
  try {
    if (isWindows) {
      const out = execSync(`netstat -ano | findstr :${port}`, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] });
      const lines = out.split(/\r?\n/);
      const pids = new Set();
      for (const line of lines) {
        const m = line.trim().match(/LISTENING\s+(\d+)$/);
        if (m) pids.add(m[1]);
      }
      for (const pid of pids) {
        try {
          execSync(`taskkill /PID ${pid} /F`, { stdio: 'pipe' });
          console.log(`   Freed port ${port} (killed PID ${pid})`);
        } catch (_) {}
      }
    } else {
      execSync(`lsof -ti:${port} | xargs kill -9 2>/dev/null`, { stdio: 'pipe' });
      console.log(`   Freed port ${port}`);
    }
  } catch (_) {
    // Port not in use or nothing to kill
  }
}

killPort(PORT);
