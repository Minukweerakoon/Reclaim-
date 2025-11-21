import { defineConfig } from 'vite'

// Make React plugin optional to avoid install/time costs in constrained envs
export default defineConfig(async () => {
  let reactPlugin: any
  try {
    // dynamically import to avoid hard failure if not installed
    const m = await import('@vitejs/plugin-react')
    reactPlugin = m.default
  } catch (e) {
    reactPlugin = undefined
  }
  return {
    plugins: reactPlugin ? [reactPlugin()] : [],
    server: {
      port: 5173
    }
  }
})
