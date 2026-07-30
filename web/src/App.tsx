import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import NavBar from '@/components/NavBar'
import GuidedFlow from '@/views/GuidedFlow'
import AgentConsole from '@/views/AgentConsole'

export default function App() {
  return (
    <BrowserRouter>
      <NavBar />
      {/* Main content â€” offset by 60px fixed header, fills remaining viewport */}
      <div style={{ paddingTop: 56, height: '100vh', boxSizing: 'border-box', display: 'flex', flexDirection: 'column' }}>
        <Routes>
          <Route path="/flow"    element={<GuidedFlow />} />
          <Route path="/console" element={<AgentConsole />} />
          <Route path="*"        element={<Navigate to="/flow" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
