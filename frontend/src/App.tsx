import { Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import NewTenantSetup from './pages/NewTenantSetup'
import AddProducts from './pages/AddProducts'
import DisableProducts from './pages/DisableProducts'
import AddSSOConnection from './pages/AddSSOConnection'
import ViewProductsByTenant from './pages/ViewProductsByTenant'
import ScanAllTenants from './pages/ScanAllTenants'
import RebasePendingChanges from './pages/RebasePendingChanges'
import AddChangelogToPending from './pages/AddChangelogToPending'
import ConfigureNachaFiles from './pages/ConfigureNachaFiles'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/new-tenant-setup" element={<NewTenantSetup />} />
      <Route path="/add-products" element={<AddProducts />} />
      <Route path="/disable-products" element={<DisableProducts />} />
      <Route path="/add-sso-connection" element={<AddSSOConnection />} />
      <Route path="/view-products-by-tenant" element={<ViewProductsByTenant />} />
      <Route path="/scan-all-tenants" element={<ScanAllTenants />} />
      <Route path="/rebase-pending-changes" element={<RebasePendingChanges />} />
      <Route path="/add-changelog-to-pending" element={<AddChangelogToPending />} />
      <Route path="/configure-nacha-files" element={<ConfigureNachaFiles />} />
    </Routes>
  )
}
