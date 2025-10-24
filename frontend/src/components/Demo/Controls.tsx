import React from 'react'
import { useAppStore } from '../../state/store'
import { Analytics, Funnel } from '../../services/analytics'

export const DemoControls: React.FC<{ onScenario?: (s: string) => void }>
  = ({ onScenario }) => {
  const { demoMode, presentationMode, toggleDemo, togglePresentation } = useAppStore()
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <label><input type="checkbox" checked={demoMode} onChange={toggleDemo} /> Demo</label>
      <label><input type="checkbox" checked={presentationMode} onChange={togglePresentation} /> Presentation</label>
      <button onClick={() => { Analytics.clear(); Funnel.start(); onScenario?.('iphone_red_library') }}>Run Scenario</button>
    </div>
  )
}

