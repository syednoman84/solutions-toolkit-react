import { useState } from 'react'
import PageLayout from '../components/PageLayout'
import ProgressBar from '../components/ProgressBar'
import ConsoleOutput from '../components/ConsoleOutput'
import { useProgressRunner } from '../hooks/useProgressRunner'
import * as api from '../api'

const steps = [
  { percent: 15, text: 'Saving configuration...' },
  { percent: 35, text: 'Cloning destination repository...' },
  { percent: 50, text: 'Creating feature branch...' },
  { percent: 70, text: 'Disabling products...' },
  { percent: 85, text: 'Committing and pushing changes...' },
  { percent: 99, text: 'Creating pull request...' },
]

export default function DisableProducts() {
  const [destRepo, setDestRepo] = useState('https://git.shared.linearft.tools/odx-platform-configs/ODXP-DPLOY--odx-config-tenantId-deploy.git')
  const [prTitle, setPrTitle] = useState('SCS-XYZ Disable Products')
  const [branchName, setBranchName] = useState('feature/SCS-XYZ-disable-products')
  const [commitMessage, setCommitMessage] = useState('Disable PCM products by automation script')
  const [productIds, setProductIds] = useState<string[]>([''])
  const runner = useProgressRunner()

  const addId = () => setProductIds([...productIds, ''])
  const removeId = (i: number) => setProductIds(productIds.filter((_, idx) => idx !== i))
  const updateId = (i: number, v: string) => { const n = [...productIds]; n[i] = v; setProductIds(n) }

  const handleRun = () => {
    if (!destRepo || !prTitle || !branchName) { alert('⚠️ All fields are required!'); return }
    const ids = productIds.filter(id => id.trim())
    if (!ids.length) { alert('⚠️ At least one Product ID is required!'); return }
    if (!confirm(`⚠️ You are about to disable ${ids.length} product(s). Continue?`)) return

    runner.run(steps, () => api.disableProductsRun(), async () => {
      await api.disableProductsSaveParams({ destRepo, prTitle, branchName, commitMessage, productIds: ids })
    })
  }

  return (
    <PageLayout title="Disable PCM Products" subtitle="Disable products for an existing tenant configuration" icon="🚫">
      <div className="content">
        <h2>🚫 Disable Products for Existing Tenant</h2>
        <div className="danger-box">
          <strong>⚠️ Warning:</strong> This will set <code>selfServiceManaged</code> to <code>false</code> in each product's
          <code>definition.json</code> and set <code>enabled</code> to <code>false</code> in <code>template_vars/agentCreation.json</code>.
        </div>
        <div className="warning-box">
          <strong>ℹ️ Note:</strong> You can find product IDs (UUIDs) by checking the <code>product/</code> directory
          in the tenant config repo, or by using the Product Summary feature from the main setup page.
        </div>

        <div className="form-group"><label>📦 Destination Repository URL (Existing Tenant)</label>
          <input value={destRepo} onChange={e => setDestRepo(e.target.value)} /></div>
        <div className="form-group"><label>📝 Pull Request Title</label>
          <input value={prTitle} onChange={e => setPrTitle(e.target.value)} /></div>
        <div className="form-group"><label>🌱 Branch Name</label>
          <input value={branchName} onChange={e => setBranchName(e.target.value)} /></div>
        <div className="form-group"><label>💬 Commit Message</label>
          <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} /></div>

        <div className="form-group">
          <div className="products-header">
            <label>🆔 Product IDs to Disable</label>
            <button type="button" className="add-btn" onClick={addId}>➕</button>
          </div>
          {productIds.map((id, i) => (
            <div className="product-id-row" key={i}>
              <input placeholder="e.g. b274f78a-0210-4242-b7e5-7e0f5ad5674b" value={id} onChange={e => updateId(i, e.target.value)} />
              <button className="remove-btn" onClick={() => removeId(i)}>×</button>
            </div>
          ))}
        </div>

        <button className="btn btn-danger" disabled={runner.running} onClick={handleRun}>🚫 Disable Products</button>
        {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} variant="danger" />}
        {runner.output && <ConsoleOutput content={runner.output} />}
      </div>
    </PageLayout>
  )
}
