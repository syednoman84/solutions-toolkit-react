import { useState } from 'react'
import PageLayout from '../components/PageLayout'
import * as api from '../api'
import type { TenantProduct } from '../types'

export default function ViewProductsByTenant() {
  const [tenantId, setTenantId] = useState('')
  const [branchName, setBranchName] = useState('master')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [products, setProducts] = useState<TenantProduct[]>([])

  const fetch = async () => {
    if (!tenantId) { alert('⚠️ Please enter a Tenant ID'); return }
    setLoading(true); setError(''); setProducts([])
    try {
      const r = await api.fetchTenantProducts(tenantId, branchName || 'master')
      if (r.error) { setError(r.error); return }
      if (!r.products?.length) { setError(`No products found for tenant "${tenantId}".`); return }
      setProducts(r.products)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally { setLoading(false) }
  }

  const types: Record<string, number> = {}
  products.forEach(p => { types[p.productType || 'Unknown'] = (types[p.productType || 'Unknown'] || 0) + 1 })

  return (
    <PageLayout title="View Products by Tenant" subtitle="Fetch and view all product definitions for a specific tenant" icon="🔍">
      <div className="content">
        <div className="info-box">
          <strong>ℹ️ Info:</strong> Enter the 3-letter tenant ID. The system will clone
          <code>ODXP-DPLOY--odx-config-&lt;tenantId&gt;-deploy</code> and read all product definitions.
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>🆔 Tenant ID (3-letter code)</label>
            <input value={tenantId} onChange={e => setTenantId(e.target.value)} placeholder="e.g. abc"
              onKeyDown={e => e.key === 'Enter' && fetch()} />
          </div>
          <div className="form-group">
            <label>🌱 Branch Name</label>
            <input value={branchName} onChange={e => setBranchName(e.target.value)} placeholder="e.g. master"
              onKeyDown={e => e.key === 'Enter' && fetch()} />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button className="btn btn-primary" disabled={loading} onClick={fetch} style={{ whiteSpace: 'nowrap' }}>
              {loading ? '⏳ Fetching...' : '🔍 Fetch Products'}
            </button>
          </div>
        </div>

        {error && <div className="error-box">❌ {error}</div>}

        {loading && (
          <div className="loading-spinner">
            <div className="spinner" />
            <p style={{ marginTop: 15 }}>Cloning repository and scanning products...</p>
          </div>
        )}

        {products.length > 0 && (
          <div style={{ marginTop: 25, overflowX: 'auto' }}>
            <div className="summary-bar">
              <div className="summary-item"><strong>{products.length}</strong> product{products.length !== 1 ? 's' : ''} found</div>
              {Object.entries(types).sort().map(([t, c]) => (
                <div className="summary-item" key={t}>{t}: <strong>{c}</strong></div>
              ))}
            </div>
            <table>
              <thead><tr><th>Product ID</th><th>Product Name</th><th>Product Type</th><th>Policy</th><th>Self Service Managed</th></tr></thead>
              <tbody>
                {products.map(p => (
                  <tr key={p.productId}>
                    <td>{p.productId}</td>
                    <td>{p.productName}</td>
                    <td>{p.productType}</td>
                    <td>{p.policy}</td>
                    <td><span className={`badge badge-${String(p.selfServiceManaged)}`}>{String(p.selfServiceManaged)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </PageLayout>
  )
}
