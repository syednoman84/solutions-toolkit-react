import { useState, useRef, useCallback } from 'react'
import PageLayout from '../components/PageLayout'
import * as api from '../api'

export default function RebasePendingChanges() {
  const [tenantId, setTenantId] = useState('')
  const [repoUrl, setRepoUrl] = useState('https://git.shared.linearft.tools/odx-platform-configs/ODXP-DPLOY--odx-config-tenantId-deploy.git')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [repoPath, setRepoPath] = useState('')
  const [products, setProducts] = useState<string[]>([])
  const [productIdx, setProductIdx] = useState(0)
  const [stepLabel, setStepLabel] = useState('')
  const [stepCmd, setStepCmd] = useState('')
  const [stepOutput, setStepOutput] = useState('')
  const [stepState, setStepState] = useState<'idle' | 'ready' | 'running' | 'done' | 'finished'>('idle')
  const [logHtml, setLogHtml] = useState('')
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

  const processProduct = useCallback((idx: number, prods: string[], rPath: string) => {
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
    pendingBranchRef.current = ''

    // Step 1: Show product
    const cmd1 = `echo "product=${product}"`
    showStep(`Step 1 — Product ID: ${product}`, cmd1, () => {
      // After step 1, continue to step 2
    })
    // We need a "continue" flow. Let's use afterExecRef for the run, then set a continueCallback
    const step2 = () => {
      const cmd = `git fetch; branch=$(git branch -a --sort=-committerdate | grep "remotes/origin/product/${product}" | grep "pending-changes" | head -n 1); branch=\${branch#"  remotes/origin/"}; if [ -z "$branch" ]; then echo "No pending changes, use master"; branch="master"; fi; echo "BRANCH=$branch"; git checkout "$branch"`
      showStep(`Step 2 — Fetch & find pending-changes branch for ${product}`, cmd, (result) => {
        const output = (result.stdout || '') + (result.stderr || '')
        const match = output.match(/BRANCH=(.+)/)
        const found = match ? match[1].trim() : 'master'
        if (found === 'master' || output.includes('No pending changes')) {
          appendLog('log-entry-skip', 'No pending-changes branch — skipping product')
          setContinue(() => () => processProduct(idx + 1, prods, rPath))
        } else {
          pendingBranchRef.current = found
          appendLog('log-entry-ok', 'Found branch: ' + found)
          setContinue(() => step3)
        }
      })
    }
    const step3 = () => {
      showStep('Step 3 — Checkout master', 'git checkout master', () => setContinue(() => step4))
    }
    const step4 = () => {
      showStep('Step 4 — Pull latest master', 'git pull origin master', () => setContinue(() => step5))
    }
    const step5 = () => {
      showStep(`Step 5 — Checkout ${pendingBranchRef.current}`, `git checkout ${pendingBranchRef.current}`, () => setContinue(() => step6))
    }
    const step6 = () => {
      showStep('Step 6 — Rebase onto master', 'git rebase master', () => setContinue(() => step7))
    }
    const step7 = () => {
      showStep('Step 7 — Force push rebased branch', 'git push --force-with-lease', () => {
        appendLog('log-entry-ok', '✅ Rebased and pushed ' + pendingBranchRef.current)
        setContinue(() => () => processProduct(idx + 1, prods, rPath))
      })
    }

    // Override afterExec for step 1 to go to step 2
    afterExecRef.current = () => setContinue(() => step2)
  }, [appendLog, showStep])

  const [continueCallback, setContinue] = useState<(() => void) | null>(null)

  const startProcess = async () => {
    if (!repoUrl) { alert('⚠️ Please enter a Repository URL'); return }
    setLoading(true); setError(''); setLogHtml(''); setStepState('idle')
    try {
      const result = await api.rebaseClone('', repoUrl)
      if (result.error) { setError(result.error); return }
      repoPathRef.current = result.repoPath
      setRepoPath(result.repoPath)
      setProducts(result.products)
      if (!result.products.length) { setError('No products found in the repository.'); return }
      appendLog('log-entry-product', `=== Cloned ${result.repoName} — ${result.products.length} product(s) found ===`)
      processProduct(0, result.products, result.repoPath)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e))
    } finally { setLoading(false) }
  }

  return (
    <PageLayout title="Rebase Pending Changes Branches" subtitle="Interactively rebase pending-changes branches onto master for each product" icon="🔀">
      <div className="content">
        <div className="info-box">
          <strong>ℹ️ Info:</strong> Enter the tenant config repository URL. The system will clone the repo, find all products,
          and for each product check if a <code>pending-changes</code> branch exists. If it does, you will interactively
          step through the rebase process.
        </div>

        <div className="form-group">
          <label>📦 Tenant Config Repository URL</label>
          <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && startProcess()} />
        </div>
        <button className="btn btn-primary" disabled={loading} onClick={startProcess}>
          {loading ? '⏳ Cloning...' : '🔀 Start'}
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
                  {stepState === 'done' && continueCallback && (
                    <button className="btn btn-primary" onClick={() => { const cb = continueCallback; setContinue(null); cb() }}>▶ Continue</button>
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
