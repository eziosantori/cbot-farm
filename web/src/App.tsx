import { Navigate, Route, Routes } from 'react-router-dom'

import AppShell from './components/AppShell'
import routeManifest from './route-manifest.json'
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
        <Route path={routeManifest.dashboard} element={<DashboardPage />} />
        <Route path={routeManifest.runDetail} element={<RunDetailPage />} />
        <Route path={routeManifest.manifestDetail} element={<ManifestDetailPage />} />
        <Route path={routeManifest.optimization} element={<OptimizationPage />} />
        <Route path={routeManifest.batches} element={<BatchesPage />} />
        <Route path={routeManifest.batchDetail} element={<BatchDetailPage />} />
        <Route path={routeManifest.simulations} element={<SimulationsPage />} />
        <Route path={routeManifest.intake} element={<StrategyIntakePage />} />
        <Route path={routeManifest.workflow} element={<WorkflowPage />} />
      </Route>
      <Route path="*" element={<Navigate to={routeManifest.dashboard} replace />} />
    </Routes>
  )
}
