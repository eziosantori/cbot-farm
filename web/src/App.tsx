import { Navigate, Route, Routes } from 'react-router-dom'

import DashboardPage from './pages/DashboardPage'
import ManifestDetailPage from './pages/ManifestDetailPage'
import RunDetailPage from './pages/RunDetailPage'
import OptimizationPage from './pages/OptimizationPage'

export default function App(): JSX.Element {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/runs/:runId" element={<RunDetailPage />} />
      <Route path="/ingestion/:manifestId" element={<ManifestDetailPage />} />
      <Route path="/optimization" element={<OptimizationPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
