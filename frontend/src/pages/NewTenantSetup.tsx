import { useState, useEffect } from 'react'
import PageLayout from '../components/PageLayout'
import ProductList from '../components/ProductList'
import ProgressBar from '../components/ProgressBar'
import ConsoleOutput from '../components/ConsoleOutput'
import { useProgressRunner } from '../hooks/useProgressRunner'
import * as api from '../api'
import type { Product } from '../types'

const setupSteps = [
  { percent: 10, text: 'Saving configuration...' },
  { percent: 20, text: 'Cloning destination repository...' },
  { percent: 35, text: 'Creating feature branch...' },
  { percent: 45, text: 'Cloning static files repository...' },
  { percent: 55, text: 'Copying baseline files...' },
  { percent: 65, text: 'Replacing placeholders in env files...' },
  { percent: 75, text: 'Creating product directories...' },
  { percent: 85, text: 'Copying template variables...' },
  { percent: 95, text: 'Committing and pushing changes...' },
  { percent: 99, text: 'Creating pull request...' },
]

export default function NewTenantSetup() {
  const [tab, setTab] = useState<'setup' | 'validate' | 'summary' | 'docs' | 'about'>('setup')
  const [destRepo, setDestRepo] = useState('')
  const [tenantDomain, setTenantDomain] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [templateTag, setTemplateTag] = useState('')
  const [prTitle, setPrTitle] = useState('')
  const [branchName, setBranchName] = useState('')
  const [commitMessage, setCommitMessage] = useState('')
  const [products, setProducts] = useState<Product[]>([])
  const [validateOutput, setValidateOutput] = useState('')
  const [summaryOutput, setSummaryOutput] = useState('')
  const [docsContent, setDocsContent] = useState('')
  const runner = useProgressRunner()

  useEffect(() => {
    api.loadParams().then(r => {
      if (r.params) {
        setDestRepo(r.params.destination_repo_github_url || '')
        setTenantDomain(r.params['tenant-domain'] || '')
        setTenantId(r.params['tenant-id'] || '')
        setTemplateTag(r.params.template_vars_tag || '')
        setPrTitle(r.params.pr_title || '')
        setBranchName(r.params.branchName || '')
        setCommitMessage(r.params.commit_message || '')
      }
      if (r.products?.length) setProducts(r.products)
    }).catch(() => {})
  }, [])

  const handleRun = () => {
    if (!destRepo || !tenantDomain || !tenantId || !templateTag || !prTitle || !branchName) {
      alert('⚠️ All fields are required!'); return
    }
    const named = products.filter(p => p.name.trim())
    if (!named.length) { alert('⚠️ At least one product is required!'); return }

    runner.run(setupSteps, () => api.runSetup(), async () => {
      await api.saveParams({
        destRepo, tenantDomain, tenantId, templateTag, prTitle, branchName, commitMessage, products: named,
      })
    })
  }

  const handleValidate = async (type: string) => {
    setValidateOutput('⏳ Running validation...\n\n')
    const r = await api.runValidation(type)
    let out = r.stdout || ''
    if (r.returncode !== 0 && r.stderr) out += '\n\n❌ Errors:\n' + r.stderr
    setValidateOutput(out)
  }

  const handleSummary = async () => {
    setSummaryOutput('⏳ Loading product summary...\n\n')
    const r = await api.runValidation('summary')
    let out = r.stdout || ''
    if (r.returncode !== 0 && r.stderr) out += '\n\n❌ Errors:\n' + r.stderr
    setSummaryOutput(out)
  }

  const handleDocs = async () => {
    const r = await api.getReadme()
    setDocsContent(r.content || 'No documentation found.')
  }

  return (
    <PageLayout title="PCM Products Setup for New Tenant" subtitle="Create products for a brand new tenant" icon="🆕">
      <div className="tabs">
        {(['setup', 'validate', 'summary', 'docs', 'about'] as const).map(t => (
          <button key={t} className={`tab${tab === t ? ' active' : ''}`} onClick={() => setTab(t)}>
            {t === 'setup' ? '🚀 Setup' : t === 'validate' ? '✅ Validate' : t === 'summary' ? '📊 Summary' : t === 'docs' ? '📖 Docs' : 'ℹ️ About'}
          </button>
        ))}
      </div>

      {tab === 'setup' && (
        <div className="content">
          <h2>🚀 Tenant Configuration Setup</h2>
          <div className="info-box"><strong>ℹ️ Info:</strong> Configure your tenant settings and products below, then run the setup script.</div>

          <div className="form-group">
            <label>📦 Destination Repository URL</label>
            <input value={destRepo} onChange={e => setDestRepo(e.target.value)} />
          </div>
          <div className="form-group">
            <label>🏢 Tenant Domain</label>
            <input value={tenantDomain} onChange={e => setTenantDomain(e.target.value)} />
          </div>
          <div className="form-group">
            <label>🆔 Tenant ID</label>
            <input value={tenantId} onChange={e => setTenantId(e.target.value)} />
          </div>
          <div className="form-group">
            <label>🏷️ Platform Tag for Default Template Vars</label>
            <input value={templateTag} onChange={e => setTemplateTag(e.target.value)} />
          </div>
          <div className="form-group">
            <label>📝 Pull Request Title</label>
            <input value={prTitle} onChange={e => setPrTitle(e.target.value)} />
          </div>
          <div className="form-group">
            <label>🌱 Branch Name</label>
            <input value={branchName} onChange={e => setBranchName(e.target.value)} />
          </div>
          <div className="form-group">
            <label>💬 Commit Message</label>
            <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} />
          </div>
          <ProductList products={products} onChange={setProducts} />
          <button className="btn btn-primary" disabled={runner.running} onClick={handleRun}>🚀 Execute</button>
          {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} />}
          {runner.output && <ConsoleOutput content={runner.output} />}
        </div>
      )}

      {tab === 'validate' && (
        <div className="content">
          <h2>✅ Validation Tools</h2>
          <div className="info-box"><strong>ℹ️ Info:</strong> Run validation scripts to verify your setup.</div>
          <button className="btn btn-success" onClick={() => handleValidate('template_vars')}>📊 Validate Template Vars</button>
          <button className="btn btn-success" onClick={() => handleValidate('env_files')}>📄 Validate Env Files</button>
          <button className="btn btn-success" onClick={() => handleValidate('all')}>✅ Validate All</button>
          {validateOutput && <div className="output">{validateOutput}</div>}
        </div>
      )}

      {tab === 'summary' && (
        <div className="content">
          <h2>📊 Product Summary</h2>
          <div className="info-box"><strong>ℹ️ Info:</strong> View all created products and their definitions.</div>
          <button className="btn btn-primary" onClick={handleSummary}>📊 Show Product Summary</button>
          {summaryOutput && <div className="output">{summaryOutput}</div>}
        </div>
      )}

      {tab === 'docs' && (
        <div className="content">
          <h2>📖 Documentation</h2>
          <button className="btn btn-primary" onClick={handleDocs}>📖 Load Documentation</button>
          {docsContent && <div className="output" style={{ marginTop: 20 }}>{docsContent}</div>}
        </div>
      )}

      {tab === 'about' && (
        <div className="content">
          <h2>ℹ️ About</h2>
          <div className="info-box">
            <h3>Solutions Toolkit for PCM Tenants</h3>
            <p style={{ marginTop: 10 }}>This tool automates the process of setting up tenant configurations by:</p>
            <ul style={{ marginLeft: 20, marginTop: 10 }}>
              <li>📥 Cloning repositories</li>
              <li>🌱 Creating feature branches</li>
              <li>📁 Creating product directories</li>
              <li>📊 Copying template variables</li>
              <li>📝 Generating definition.json files</li>
              <li>✅ Committing and pushing changes</li>
              <li>📤 Creating pull requests</li>
            </ul>
          </div>
          <h3 style={{ marginTop: 20 }}>🏷️ Supported Product Types</h3>
          <ul style={{ marginLeft: 20, marginTop: 10 }}>
            <li><strong>Consumer_CC</strong> - Consumer Credit Card Self Service</li>
            <li><strong>Consumer_DAO</strong> - Consumer Deposit Account Opening</li>
            <li><strong>SMB_DAO</strong> - Small Business Deposit Account Opening</li>
            <li><strong>SMB_CC</strong> - Small Business Credit Card</li>
            <li><strong>SMB_LOC</strong> - Small Business Line of Credit</li>
            <li><strong>SMB_TL</strong> - Small Business Term Loan</li>
          </ul>
          <h3 style={{ marginTop: 20 }}>🛠️ Prerequisites</h3>
          <ul style={{ marginLeft: 20, marginTop: 10 }}>
            <li>Python 3.6+</li>
            <li>Git CLI</li>
            <li>GitHub CLI (gh)</li>
            <li>Access to required repositories</li>
          </ul>
        </div>
      )}
    </PageLayout>
  )
}
