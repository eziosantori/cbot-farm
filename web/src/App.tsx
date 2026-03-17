import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from './components/AppShell'
import DashboardPage from './pages/DashboardPage'
import ManifestDetailPage from './pages/ManifestDetailPage'
import RunDetailPage from './pages/RunDetailPage'
import OptimizationPage from './pages/OptimizationPage'
import BatchesPage from './pages/BatchesPage'
import BatchDetailPage from './pages/BatchDetailPage'
import SimulationsPage from './pages/SimulationsPage'
import StrategyIntakePage from './pages/StrategyIntakePage'
import WorkflowPage from './pages/WorkflowPage'

export default function App(): JSX.Element {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/runs/:runId" element={<RunDetailPage />} />
        <Route path="/ingestion/:manifestId" element={<ManifestDetailPage />} />
        <Route path="/optimization" element={<OptimizationPage />} />
        <Route path="/batches" element={<BatchesPage />} />
        <Route path="/batches/:batchId" element={<BatchDetailPage />} />
        <Route path="/simulations" element={<SimulationsPage />} />
        <Route path="/intake" element={<StrategyIntakePage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
