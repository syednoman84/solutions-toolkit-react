import { useState, useRef, useCallback } from 'react'
import PageLayout from '../components/PageLayout'
import * as api from '../api'

export default function AddChangelogToPending() {
  const [tenantId, setTenantId] = useState('')
  const [repoUrl, setRepoUrl] = useState('https://git.shared.linearft.tools/odx-platform-configs/ODXP-DPLOY--odx-config-tenantId-deploy.git')
  const [jsonContent, setJsonContent] = useState('')
  const [commitMessage, setCommitMessage] = useState('Add changelog file')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [products, setProducts] = useState<string[]>([])
  const [productIdx, setProductIdx] = useState(0)
  const [stepLabel, setStepLabel] = useState('')
  const [stepCmd, setStepCmd] = useState('')
  const [stepOutput, setStepOutput] = useState('')
  const [stepState, setStepState] = useState<'idle' | 'ready' | 'running' | 'done' | 'finished' | 'creating'>('idle')
  const [logHtml, setLogHtml] = useState('')
  const [continueCallback, setContinue] = useState<(() => void) | null>(null)
  const afterExecRef = useRef<((r: { stdout?: string; stderr?: string }) => void) | null>(null)
  const pendingBranchRef = useRef('')
  const repoPathRef = useRef('')

  const appendLog = useCallback((cls: string, text: string) => {
    setLogHtml(prev => prev + `<span class="${cls}">${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</span>\n`)
  }, [])

  const showStep = useCallback((label: string, cmd: string, afterExec: (r: { stdout?: string; stderr?: string }) => void) => {
    setStepLabel(label); setStepCmd(cmd); setStepOutput(''); setStepState('ready')
    afterExecRef.current = afterExec
  }, [])

  const executeStep = useCallback(async () => {
    setStepState('running')
    try {
      const result = await api.rebaseRunCommand(repoPathRef.current, stepCmd)
      let out = ''
      if (result.stdout) out += result.stdout
      if (result.stderr) out += result.stderr
      setStepOutput(out || '(no output)')
      appendLog('log-entry-cmd', '$ ' + stepCmd)
      if (result.stdout) appendLog('log-entry-ok', result.stdout)
      if (result.stderr) appendLog('log-entry-err', result.stderr)
      setStepState('done')
      afterExecRef.current?.(result)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e)
      setStepOutput('Error: ' + msg)
      appendLog('log-entry-err', 'Error: ' + msg)
      setStepState('done')
    }
  }, [stepCmd, appendLog])

  const processProduct = useCallback((idx: number, prods: string[]) => {
    if (idx >= prods.length) {
      setProductIdx(prods.length)
      setStepLabel('✅ All products processed!')
      setStepState('finished')
      appendLog('log-entry-product', '=== All products processed ===')
      return
    }
    const product = prods[idx]
    setProductIdx(idx + 1)
    appendLog('log-entry-product', `\n--- Product ${idx + 1}/${prods.length}: ${product} ---`)

    const cmd1 = `echo "product=${product}"`
    showStep(`Step 1 — Product ID: ${product}`, cmd1, () => {
      // After run, show continue + skip
    })
    afterExecRef.current = () => {
      setContinue(null)
      setStepState('done')
      // Show both continue and skip
      setContinueWithSkip(
        () => step2(product, idx, prods),
        () => { appendLog('log-entry-skip', 'Skipped product ' + product); processProduct(idx + 1, prods) }
      )
    }

    const step2 = (prod: string, i: number, ps: string[]) => {
      const cmd = `git fetch; branch=$(git branch -a --sort=-committerdate | grep "remotes/origin/product/${prod}" | grep "pending-changes" | head -n 1); branch=\${branch#"  remotes/origin/"}; if [ -z "$branch" ]; then echo "No pending changes, use master"; branch="master"; fi; echo "BRANCH=$branch"; git checkout "$branch"`
      showStep(`Step 2 — Fetch & find pending-changes branch for ${prod}`, cmd, (result) => {
        const output = (result.stdout || '') + (result.stderr || '')
        const match = output.match(/BRANCH=(.+)/)
        const found = match ? match[1].trim() : 'master'
        if (found === 'master' || output.includes('No pending changes')) {
          appendLog('log-entry-skip', 'No pending-changes branch — skipping product')
          setContinue(() => () => processProduct(i + 1, ps))
        } else {
          pendingBranchRef.current = found
          appendLog('log-entry-ok', 'Found branch: ' + found)
          setContinue(() => () => step3_createChangelog(prod, i, ps))
        }
      })
    }

    const step3_createChangelog = async (prod: string, i: number, ps: string[]) => {
      setStepLabel(`Step 3 — Create changelog file in product/${prod}/amt-product-config-bff/changes/`)
      setStepCmd('Creating <uuid>.json with provided JSON content...')
      setStepOutput(''); setStepState('creating')
      try {
        const result = await api.createChangelog(repoPathRef.current, prod, jsonContent)
        if (result.error) {
          setStepOutput('Error: ' + result.error)
          appendLog('log-entry-err', 'Failed to create changelog: ' + result.error)
          setStepState('done')
          setContinue(() => () => processProduct(i + 1, ps))
        } else {
          setStepOutput('✅ Created: ' + result.relativePath)
          appendLog('log-entry-ok', 'Created: ' + result.relativePath)
          setStepState('done')
          setContinue(() => () => step4_commit(result.relativePath, i, ps))
        }
      } catch (e: unknown) {
        setStepOutput('Error: ' + (e instanceof Error ? e.message : String(e)))
        setStepState('done')
        setContinue(() => () => processProduct(i + 1, ps))
      }
    }

    const step4_commit = (relPath: string, i: number, ps: string[]) => {
      const cmd = `git add "${relPath}" && git commit -m "${commitMessage.replace(/"/g, '\\"')}"`
      showStep('Step 4 — Git add & commit', cmd, () => setContinue(() => () => step5_push(i, ps)))
    }

    const step5_push = (i: number, ps: string[]) => {
      showStep('Step 5 — Git push', 'git push', () => {
        appendLog('log-entry-ok', '✅ Pushed changelog to ' + pendingBranchRef.current)
        setContinue(() => () => processProduct(i + 1, ps))
      })
    }
  }, [appendLog, showStep, jsonContent, commitMessage])

  const [skipCallback, setSkipCallback] = useState<(() => void) | null>(null)
  const setContinueWithSkip = (cont: () => void, skip: () => void) => {
    setContinue(() => cont); setSkipCallback(() => skip)
  }

  const startProcess = async () => {
    if (!repoUrl) { alert('⚠️ Please enter a Repository URL'); return }
    if (!jsonContent) { alert('⚠️ Please enter the changelog JSON content'); return }
    if (!commitMessage) { alert('⚠️ Please enter a commit message'); return }
    try { JSON.parse(jsonContent) } catch (e: unknown) { alert('⚠️ Invalid JSON: ' + (e instanceof Error ? e.message : String(e))); return }

    setLoading(true); setError(''); setLogHtml(''); setStepState('idle'); setSkipCallback(null)
    try {
      const result = await api.rebaseClone('', repoUrl)
      if (result.error) { setError(result.error); return }
      repoPathRef.current = result.repoPath
      setProducts(result.products)
      if (!result.products.length) { setError('No products found.'); return }
      appendLog('log-entry-product', `=== Cloned ${result.repoName} — ${result.products.length} product(s) found ===`)
      processProduct(0, result.products)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally { setLoading(false) }
  }

  return (
    <PageLayout title="Add Change Log File to Pending-Changes Branches" subtitle="Add a changelog JSON file to each product's pending-changes branch" icon="📝">
      <div className="content">
        <div className="info-box">
          <strong>ℹ️ Info:</strong> Enter the tenant config repository URL and the JSON content for the changelog file.
          For each product with a <code>pending-changes</code> branch, the system will create
          <code>amt-product-config-bff/changes/&lt;uuid&gt;.json</code> inside the product directory, commit and push it.
        </div>

        <div className="form-group">
          <label>📦 Tenant Config Repository URL</label>
          <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)} />
        </div>
        <div className="form-group">
          <label>📄 Changelog JSON Content</label>
          <textarea value={jsonContent} onChange={e => setJsonContent(e.target.value)} placeholder={'{\n  "key": "value"\n}'} />
        </div>
        <div className="form-group">
          <label>💬 Commit Message</label>
          <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} />
        </div>

        <button className="btn btn-primary" disabled={loading} onClick={startProcess}>
          {loading ? '⏳ Cloning...' : '📝 Start'}
        </button>

        {error && <div className="error-box">❌ {error}</div>}
        {loading && <div className="loading-spinner"><div className="spinner" /><p style={{ marginTop: 15 }}>Cloning repository and discovering products...</p></div>}

        {products.length > 0 && stepState !== 'idle' && (
          <div style={{ marginTop: 25 }}>
            <div style={{ background: '#f8f9fa', border: '2px solid #e9ecef', borderRadius: 8, padding: '15px 20px', marginBottom: 15 }}>
              <div style={{ fontWeight: 600, color: '#495057', fontSize: '0.95em' }}>Product {productIdx} / {products.length}</div>
              <div style={{ width: '100%', height: 10, background: '#e9ecef', borderRadius: 5, marginTop: 8, overflow: 'hidden' }}>
                <div style={{ height: '100%', background: 'linear-gradient(90deg, #0284c7 0%, #075985 100%)', width: `${products.length > 0 ? (productIdx / products.length * 100) : 0}%`, transition: 'width 0.4s ease' }} />
              </div>
            </div>

            {stepState === 'finished' ? (
              <div className="step-card done"><div className="step-label">{stepLabel}</div></div>
            ) : (
              <div className="step-card active">
                <div className="step-label">{stepLabel}</div>
                <div className="step-command">$ {stepCmd}</div>
                {stepOutput && <div className="step-output">{stepOutput}</div>}
                <div className="step-actions">
                  {stepState === 'ready' && <button className="btn btn-success" onClick={executeStep}>▶ Run</button>}
                  {stepState === 'running' && <span style={{ color: '#6c757d' }}>⏳ Running...</span>}
                  {stepState === 'creating' && <span style={{ color: '#6c757d' }}>⏳ Creating file...</span>}
                  {stepState === 'done' && continueCallback && (
                    <>
                      <button className="btn btn-primary" onClick={() => { const cb = continueCallback; setContinue(null); setSkipCallback(null); cb() }}>▶ Continue</button>
                      {skipCallback && <button className="btn btn-skip" onClick={() => { const cb = skipCallback; setContinue(null); setSkipCallback(null); cb() }}>⏭ Skip this product</button>}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {logHtml && (
          <div style={{ marginTop: 25 }}>
            <h3 style={{ color: '#495057', marginBottom: 10 }}>📋 Full Log</h3>
            <div className="full-log" dangerouslySetInnerHTML={{ __html: logHtml }} />
          </div>
        )}
      </div>
    </PageLayout>
  )
}
