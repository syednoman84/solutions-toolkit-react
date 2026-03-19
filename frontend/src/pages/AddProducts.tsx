import { useState, useEffect } from 'react'
import PageLayout from '../components/PageLayout'
import ProductList from '../components/ProductList'
import ProgressBar from '../components/ProgressBar'
import ConsoleOutput from '../components/ConsoleOutput'
import { useProgressRunner } from '../hooks/useProgressRunner'
import * as api from '../api'
import type { Product } from '../types'

const steps = [
  { percent: 15, text: 'Saving configuration...' },
  { percent: 30, text: 'Cloning destination repository...' },
  { percent: 45, text: 'Creating feature branch...' },
  { percent: 60, text: 'Cloning template variables repository...' },
  { percent: 75, text: 'Creating product directories...' },
  { percent: 85, text: 'Copying template variables...' },
  { percent: 95, text: 'Committing and pushing changes...' },
  { percent: 99, text: 'Creating pull request...' },
]

export default function AddProducts() {
  const [tab, setTab] = useState<'setup' | 'validate' | 'summary'>('setup')
  const [destRepo, setDestRepo] = useState('')
  const [templateTag, setTemplateTag] = useState('')
  const [prTitle, setPrTitle] = useState('')
  const [branchName, setBranchName] = useState('')
  const [commitMessage, setCommitMessage] = useState('Add new PCM products to existing tenant by automation script')
  const [products, setProducts] = useState<Product[]>([])
  const [validateOutput, setValidateOutput] = useState('')
  const [summaryOutput, setSummaryOutput] = useState('')
  const runner = useProgressRunner()

  useEffect(() => {
    api.addProductsLoadParams().then(r => {
      if (r.params) {
        setDestRepo(r.params.destination_repo_github_url || '')
        setTemplateTag(r.params.template_vars_tag || '')
        setPrTitle(r.params.pr_title || '')
        setBranchName(r.params.branchName || '')
      }
      if (r.products?.length) setProducts(r.products)
    }).catch(() => {})
  }, [])

  const handleRun = () => {
    if (!destRepo || !templateTag || !prTitle || !branchName) { alert('⚠️ All fields are required!'); return }
    const named = products.filter(p => p.name.trim())
    if (!named.length) { alert('⚠️ At least one product is required!'); return }

    runner.run(steps, () => api.addProductsRun(), async () => {
      await api.addProductsSaveParams({ destRepo, templateTag, prTitle, branchName, commitMessage, products: named })
    })
  }

  return (
    <PageLayout title="Add PCM Products for Existing Tenant" subtitle="Add new products to an existing tenant configuration" icon="➕">
      <div className="tabs">
        {(['setup', 'validate', 'summary'] as const).map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {t === 'setup' ? '🚀 Add Products' : t === 'validate' ? '✅ Validate' : '📊 Summary'}
          </button>
        ))}
      </div>

      {tab === 'setup' && (
        <div className="content">
          <h2>➕ Add New Products to Existing Tenant</h2>
          <div className="warning-box">
            <strong>⚠️ Note:</strong> This will only add new products under the <code>product/</code> directory.
            It will <strong>not</strong> modify app, env, or .gitignore files. The tenant must already be set up.
          </div>
          <div className="form-group"><label>📦 Destination Repository URL (Existing Tenant)</label>
            <input value={destRepo} onChange={e => setDestRepo(e.target.value)} /></div>
          <div className="form-group"><label>🏷️ Platform Tag for Default Template Vars</label>
            <input value={templateTag} onChange={e => setTemplateTag(e.target.value)} /></div>
          <div className="form-group"><label>📝 Pull Request Title</label>
            <input value={prTitle} onChange={e => setPrTitle(e.target.value)} /></div>
          <div className="form-group"><label>🌱 Branch Name</label>
            <input value={branchName} onChange={e => setBranchName(e.target.value)} /></div>
          <div className="form-group"><label>💬 Commit Message</label>
            <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} /></div>
          <ProductList products={products} onChange={setProducts} />
          <button className="btn btn-primary" disabled={runner.running} onClick={handleRun}>➕ Add Products</button>
          {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} />}
          {runner.output && <ConsoleOutput content={runner.output} />}
        </div>
      )}

      {tab === 'validate' && (
        <div className="content">
          <h2>✅ Validation Tools</h2>
          <div className="info-box"><strong>ℹ️ Info:</strong> Run validation scripts to verify the newly added products.</div>
          <button className="btn btn-success" onClick={async () => {
            setValidateOutput('⏳ Running validation...\n\n')
            const r = await api.runValidation('template_vars')
            setValidateOutput((r.stdout || '') + (r.returncode !== 0 && r.stderr ? '\n\n❌ Errors:\n' + r.stderr : ''))
          }}>📊 Validate Template Vars</button>
          {validateOutput && <div className="output">{validateOutput}</div>}
        </div>
      )}

      {tab === 'summary' && (
        <div className="content">
          <h2>📊 Product Summary</h2>
          <div className="info-box"><strong>ℹ️ Info:</strong> View all products (existing + newly added) and their definitions.</div>
          <button className="btn btn-primary" onClick={async () => {
            setSummaryOutput('⏳ Loading product summary...\n\n')
            const r = await api.runValidation('summary')
            setSummaryOutput((r.stdout || '') + (r.returncode !== 0 && r.stderr ? '\n\n❌ Errors:\n' + r.stderr : ''))
          }}>📊 Show Product Summary</button>
          {summaryOutput && <div className="output">{summaryOutput}</div>}
        </div>
      )}
    </PageLayout>
  )
}
