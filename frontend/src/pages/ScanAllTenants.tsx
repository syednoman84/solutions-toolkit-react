import { useState, useCallback } from 'react'
import PageLayout from '../components/PageLayout'
import ProgressBar from '../components/ProgressBar'
import ConsoleOutput from '../components/ConsoleOutput'
import { useProgressRunner } from '../hooks/useProgressRunner'
import * as api from '../api'

const steps = [
  { percent: 10, text: 'Fetching repository list from GitHub Enterprise...' },
  { percent: 25, text: 'Cloning and scanning tenant repositories...' },
  { percent: 50, text: 'Extracting product definitions...' },
  { percent: 75, text: 'Analyzing product configurations...' },
  { percent: 90, text: 'Generating reports...' },
  { percent: 99, text: 'Finalizing...' },
]

export default function ScanAllTenants() {
  const [repoLimit, setRepoLimit] = useState(1000)
  const [cleanup, setCleanup] = useState(true)
  const [resultTab, setResultTab] = useState<'definitions' | 'count' | 'types'>('definitions')
  const [reports, setReports] = useState<Record<string, string>>({})
  const [showResults, setShowResults] = useState(false)
  const [openRepos, setOpenRepos] = useState<Set<string>>(new Set())
  const runner = useProgressRunner()

  const loadReports = useCallback(async () => {
    const [defs, count, types] = await Promise.all([
      api.scanTenantsResults('definitions'),
      api.scanTenantsResults('count'),
      api.scanTenantsResults('types'),
    ])
    setReports({
      definitions: defs.content || defs.error || '',
      count: count.content || count.error || '',
      types: types.content || types.error || '',
    })
    setShowResults(true)
  }, [])

  const handleScan = () => {
    runner.run(steps, () => api.scanTenantsRun(repoLimit, cleanup)).then(ok => { if (ok) loadReports() })
  }

  const toggleRepo = (repo: string) => {
    setOpenRepos(prev => { const n = new Set(prev); n.has(repo) ? n.delete(repo) : n.add(repo); return n })
  }
  const toggleAll = (expand: boolean) => {
    if (!reports.definitions) return
    try {
      const data = JSON.parse(reports.definitions)
      setOpenRepos(expand ? new Set(Object.keys(data)) : new Set())
    } catch { /* ignore */ }
  }

  const renderDefinitions = () => {
    try {
      const data = JSON.parse(reports.definitions || '{}')
      const repos = Object.keys(data).sort()
      if (!repos.length) return <div style={{ textAlign: 'center', color: '#adb5bd', padding: 30 }}>No product definitions found.</div>
      return (
        <>
          <div style={{ marginBottom: 10, display: 'flex', gap: 8 }}>
            <button onClick={() => toggleAll(true)} style={{ padding: '5px 14px', border: '1px solid #0284c7', borderRadius: 5, background: 'white', color: '#0284c7', cursor: 'pointer', fontSize: '0.8em', fontWeight: 600 }}>▼ Expand All</button>
            <button onClick={() => toggleAll(false)} style={{ padding: '5px 14px', border: '1px solid #0284c7', borderRadius: 5, background: 'white', color: '#0284c7', cursor: 'pointer', fontSize: '0.8em', fontWeight: 600 }}>▲ Collapse All</button>
          </div>
          {repos.map(repo => {
            const prods = data[repo]
            const isOpen = openRepos.has(repo)
            return (
              <div className="repo-accordion" key={repo}>
                <div className={`repo-header${isOpen ? ' open' : ''}`} onClick={() => toggleRepo(repo)}>
                  <span className="chevron">▶</span>
                  {repo}
                  <span className="product-count">{prods.length} product{prods.length !== 1 ? 's' : ''}</span>
                </div>
                <div className={`repo-body${isOpen ? ' open' : ''}`}>{JSON.stringify(prods, null, 2)}</div>
              </div>
            )
          })}
        </>
      )
    } catch {
      return <pre style={{ whiteSpace: 'pre-wrap' }}>{reports.definitions}</pre>
    }
  }

  const getProductTypeCounts = useCallback((): Record<string, number> => {
    try {
      const data = JSON.parse(reports.definitions || '{}')
      const counts: Record<string, number> = {}
      for (const repo of Object.keys(data)) {
        for (const prod of data[repo]) {
          const t = prod.productType || 'Unknown'
          counts[t] = (counts[t] || 0) + 1
        }
      }
      return counts
    } catch { return {} }
  }, [reports.definitions])

  const renderHistogram = () => {
    const counts = getProductTypeCounts()
    const entries = Object.entries(counts).sort((a, b) => b[1] - a[1])
    if (!entries.length) return null
    const max = entries[0][1]
    const total = entries.reduce((s, [, v]) => s + v, 0)
    const colors = ['#0284c7', '#0369a1', '#075985', '#0ea5e9', '#38bdf8', '#7dd3fc', '#60a5fa', '#818cf8']
    return (
      <div style={{ marginBottom: 20, padding: 20, background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
        <h4 style={{ color: '#334155', marginBottom: 15, fontSize: '0.95em' }}>📊 Product Type Distribution ({total} total)</h4>
        {entries.map(([type, count], i) => (
          <div key={type} style={{ display: 'flex', alignItems: 'center', marginBottom: 8, gap: 10 }}>
            <div style={{ width: 160, fontSize: '0.82em', color: '#475569', textAlign: 'right', flexShrink: 0 }}>{type}</div>
            <div style={{ flex: 1, background: '#e2e8f0', borderRadius: 4, height: 22, overflow: 'hidden' }}>
              <div style={{
                width: `${(count / max) * 100}%`, height: '100%',
                background: colors[i % colors.length], borderRadius: 4,
                display: 'flex', alignItems: 'center', paddingLeft: 8,
                color: 'white', fontSize: '0.78em', fontWeight: 600, minWidth: 30,
              }}>{count}</div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <PageLayout title="Scan All Tenants" subtitle="Scan all tenant repositories and analyze product configurations" icon="📊">
      <div className="content">
        <div className="info-box">
          <strong>ℹ️ Info:</strong> This tool scans all tenant repositories in the <code>odx-platform-configs</code> organization,
          extracts product definitions, and generates three reports. Requires <code>gh</code> CLI authenticated with GitHub Enterprise.
        </div>

        <div className="form-row" style={{ alignItems: 'flex-end' }}>
          <div className="form-group">
            <label>🔢 Repository Limit</label>
            <input type="number" value={repoLimit} onChange={e => setRepoLimit(Number(e.target.value))} min={1} max={5000} />
          </div>
          <div className="form-group">
            <label>🧹 Cleanup Cloned Repos</label>
            <select value={String(cleanup)} onChange={e => setCleanup(e.target.value === 'true')}>
              <option value="true">Yes - Delete after scanning</option>
              <option value="false">No - Keep cloned repos</option>
            </select>
          </div>
        </div>

        <button className="btn btn-primary" disabled={runner.running} onClick={handleScan}>
          {runner.running ? '⏳ Scanning...' : '📊 Start Scan'}
        </button>

        {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} />}
        {runner.output && <ConsoleOutput content={runner.output} dark />}

        {showResults && (
          <div style={{ marginTop: 25 }}>
            {renderHistogram()}
            <h3 style={{ color: '#495057', marginBottom: 0 }}>📁 Generated Reports</h3>
            <div className="result-tabs">
              {(['definitions', 'count', 'types'] as const).map(t => (
                <button key={t} className={`result-tab${resultTab === t ? ' active' : ''}`} onClick={() => setResultTab(t)}>
                  {t === 'definitions' ? '📄 Product Definitions (JSON)' : t === 'count' ? '📊 Products Count by Tenant' : '🏷️ Product Types by Tenant'}
                </button>
              ))}
            </div>
            <div className="result-content">
              {resultTab === 'definitions' && renderDefinitions()}
              {resultTab === 'count' && <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'Courier New', monospace", fontSize: '0.85em', lineHeight: 1.6 }}>{reports.count}</pre>}
              {resultTab === 'types' && <pre style={{ whiteSpace: 'pre-wrap', fontFamily: "'Courier New', monospace", fontSize: '0.85em', lineHeight: 1.6 }}>{reports.types}</pre>}
            </div>
          </div>
        )}
      </div>
    </PageLayout>
  )
}
