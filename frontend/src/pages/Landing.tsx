import { Link } from 'react-router-dom'

const workflows = [
  { to: '/new-tenant-setup', icon: '🆕', title: 'PCM Products Setup', subtitle: 'for New Tenant', desc: 'Create products for a brand new tenant' },
  { to: '/add-products', icon: '➕', title: 'Add PCM Products', subtitle: 'for Existing Tenant', desc: 'Add new products to existing tenant' },
  { to: '/disable-products', icon: '🚫', title: 'Disable PCM Products', subtitle: 'for Existing Tenant', desc: 'Disable products for a tenant' },
  { to: '/add-sso-connection', icon: '🔐', title: 'Add SSO Connection', subtitle: 'for Existing Tenant', desc: 'Add SSO connection configuration' },
  { to: '/rebase-pending-changes', icon: '🔀', title: 'Rebase Pending Changes Branches', subtitle: '', desc: 'Interactively rebase pending-changes branches onto master' },
  { to: '/add-changelog-to-pending', icon: '📝', title: 'Add Change Log File', subtitle: 'to Pending-Changes Branches', desc: 'Add a changelog JSON file to each product\'s pending-changes branch' },
  { to: '/view-products-by-tenant', icon: '🔍', title: 'View Products by Tenant', subtitle: '', desc: 'Fetch and view all products for a specific tenant' },
  { to: '/scan-all-tenants', icon: '📊', title: 'Scan All Tenants', subtitle: '', desc: 'Provides details of all the products used by Tenants' },
  { to: '/configure-nacha-files', icon: '💳', title: 'Configure NACHA Files', subtitle: '', desc: 'Add NACHA payment gateway configuration files to a tenant' },
]

export default function Landing() {
  return (
    <div className="container">
      <div className="header">
        <h1>PCM Tenants Configuration Toolkit</h1>
        <p>Automated tenant configuration management with validation</p>
      </div>
      <div className="landing-page">
        <div className="button-grid">
          {workflows.map(w => (
            <Link key={w.to} to={w.to} className="landing-btn">
              <div className="landing-btn-icon">{w.icon}</div>
              <div className="landing-btn-title">{w.title}</div>
              {w.subtitle && <div className="landing-btn-title">{w.subtitle}</div>}
              <div className="landing-btn-desc">{w.desc}</div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
