import { useState, useEffect } from 'react'
import PageLayout from '../components/PageLayout'
import ProgressBar from '../components/ProgressBar'
import ConsoleOutput from '../components/ConsoleOutput'
import { useProgressRunner } from '../hooks/useProgressRunner'
import * as api from '../api'

const steps = [
  { percent: 15, text: 'Writing NACHA configuration files...' },
  { percent: 35, text: 'Staging changes...' },
  { percent: 55, text: 'Committing changes...' },
  { percent: 75, text: 'Pushing to remote...' },
  { percent: 90, text: 'Creating pull request...' },
  { percent: 99, text: 'Finalizing...' },
]

export default function ConfigureNachaFiles() {
  const [repoUrl, setRepoUrl] = useState('https://git.shared.linearft.tools/odx-platform-configs/ODXP-DPLOY--odx-config-tenantId-deploy.git')
  const [branchName, setBranchName] = useState('feature/SCS-XYZ-nacha-config')
  const [prTitle, setPrTitle] = useState('SCS-XYZ Add NACHA Configuration')
  const [commitMessage, setCommitMessage] = useState('Add NACHA configuration files')
  const [repoPath, setRepoPath] = useState('')
  const [cloning, setCloning] = useState(false)
  const [cloneError, setCloneError] = useState('')
  const [cloned, setCloned] = useState(false)

  // JSON editors
  const [fileOptionsJson, setFileOptionsJson] = useState('')
  const [vendorJson, setVendorJson] = useState('')
  const [nachaPgJson, setNachaPgJson] = useState('')
  const [serenityprdprJson, setSerenityprdprJson] = useState('')
  const [serenityprod1Json, setSerenityprod1Json] = useState('')
  const [hasSerenityprdpr, setHasSerenityprdpr] = useState(false)
  const [hasSerenityprod1, setHasSerenityprod1] = useState(false)

  // Track original env content to detect changes
  const [origSerenityprdpr, setOrigSerenityprdpr] = useState('')
  const [origSerenityprod1, setOrigSerenityprod1] = useState('')

  // JSON validation
  const [jsonErrors, setJsonErrors] = useState<Record<string, string>>({})

  const runner = useProgressRunner()

  // Load defaults on mount
  useEffect(() => {
    api.nachaDefaults().then(d => {
      setFileOptionsJson(d.fileOptions || '{}')
      setVendorJson(d.vendor || '{}')
      setNachaPgJson(d.nachaPg || '{}')
    }).catch(() => {})
  }, [])

  const validateJson = (key: string, value: string): boolean => {
    try {
      JSON.parse(value)
      setJsonErrors(prev => { const n = { ...prev }; delete n[key]; return n })
      return true
    } catch (e: unknown) {
      setJsonErrors(prev => ({ ...prev, [key]: e instanceof Error ? e.message : String(e) }))
      return false
    }
  }

  const handleClone = async () => {
    if (!repoUrl || !branchName) { alert('⚠️ Repository URL and Branch Name are required'); return }
    setCloning(true); setCloneError(''); setCloned(false); setRepoPath('')
    setHasSerenityprdpr(false); setHasSerenityprod1(false)
    setSerenityprdprJson(''); setSerenityprod1Json('')
    setOrigSerenityprdpr(''); setOrigSerenityprod1('')
    try {
      const result = await api.nachaClone(repoUrl, branchName)
      if (result.error) { setCloneError(result.error); return }
      setRepoPath(result.repoPath)
      setCloned(true)
      if (result.envFiles.serenityprdpr) {
        setHasSerenityprdpr(true)
        setSerenityprdprJson(result.envFiles.serenityprdpr)
        setOrigSerenityprdpr(result.envFiles.serenityprdpr)
      }
      if (result.envFiles.serenityprod1) {
        setHasSerenityprod1(true)
        setSerenityprod1Json(result.envFiles.serenityprod1)
        setOrigSerenityprod1(result.envFiles.serenityprod1)
      }
    } catch (e: unknown) {
      setCloneError(e instanceof Error ? e.message : String(e))
    } finally { setCloning(false) }
  }

  const handleRun = () => {
    if (!repoPath) { alert('⚠️ Please clone the repository first'); return }
    if (!prTitle || !commitMessage || !branchName) { alert('⚠️ All fields are required'); return }

    // Validate all JSON
    const checks = [
      validateJson('fileOptions', fileOptionsJson),
      validateJson('vendor', vendorJson),
      validateJson('nachaPg', nachaPgJson),
    ]
    if (hasSerenityprdpr && serenityprdprJson) checks.push(validateJson('serenityprdpr', serenityprdprJson))
    if (hasSerenityprod1 && serenityprod1Json) checks.push(validateJson('serenityprod1', serenityprod1Json))

    if (checks.some(c => !c)) { alert('⚠️ Please fix JSON errors before running'); return }

    runner.run(steps, () => api.nachaRun({
      repoPath, prTitle, commitMessage, branchName,
      fileOptionsJson, vendorJson, nachaPgJson,
      serenityprdprJson: hasSerenityprdpr && serenityprdprJson !== origSerenityprdpr ? serenityprdprJson : undefined,
      serenityprod1Json: hasSerenityprod1 && serenityprod1Json !== origSerenityprod1 ? serenityprod1Json : undefined,
    }))
  }

  const handleReset = () => {
    setRepoPath(''); setCloned(false); setCloneError('')
    setHasSerenityprdpr(false); setHasSerenityprod1(false)
    setSerenityprdprJson(''); setSerenityprod1Json('')
    setOrigSerenityprdpr(''); setOrigSerenityprod1('')
    setJsonErrors({})
    api.nachaDefaults().then(d => {
      setFileOptionsJson(d.fileOptions || '{}')
      setVendorJson(d.vendor || '{}')
      setNachaPgJson(d.nachaPg || '{}')
    }).catch(() => {})
  }

  return (
    <PageLayout title="Configure NACHA Files" subtitle="Add NACHA payment gateway configuration files to a tenant repository" icon="💳">
      <div className="content">
        <div className="info-box">
          <strong>ℹ️ Info:</strong> This tool clones the tenant config repository, creates a feature branch,
          and adds NACHA configuration files (<code>file_options.json</code>, <code>vendor.json</code>,
          <code>nachaPg.json</code>) along with any existing env files. All changes are committed and a PR is created.
        </div>

        <h2>💳 Repository Configuration</h2>
        <div className="form-group"><label>📦 Tenant Config Repository URL</label>
          <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)} disabled={cloned} /></div>
        <div className="form-group"><label>🌱 Feature Branch Name</label>
          <input value={branchName} onChange={e => setBranchName(e.target.value)} disabled={cloned} /></div>
        <div className="form-group"><label>📝 Pull Request Title</label>
          <input value={prTitle} onChange={e => setPrTitle(e.target.value)} /></div>
        <div className="form-group"><label>💬 Commit Message</label>
          <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} /></div>

        {!cloned ? (
          <button className="btn btn-primary" disabled={cloning} onClick={handleClone}>
            {cloning ? '⏳ Cloning...' : '📥 Clone & Load Configs'}
          </button>
        ) : (
          <button className="btn btn-secondary" onClick={handleReset} style={{ background: '#6c757d', color: 'white', border: 'none', padding: '10px 20px', borderRadius: 6, cursor: 'pointer' }}>
            🔄 Start Fresh
          </button>
        )}

        {cloneError && <div className="error-box" style={{ marginTop: 10 }}>❌ {cloneError}</div>}
        {cloning && <div className="loading-spinner"><div className="spinner" /><p style={{ marginTop: 15 }}>Cloning repository and loading configs...</p></div>}

        {cloned && (
          <>
            <div style={{ marginTop: 20, padding: '10px 15px', background: '#d4edda', border: '1px solid #c3e6cb', borderRadius: 6, color: '#155724' }}>
              ✅ Repository cloned and branch <code>{branchName}</code> checked out.
            </div>

            <h2 style={{ marginTop: 25 }}>📄 NACHA Configuration Files</h2>

            <div className="form-group">
              <label>📁 app/payment-gateway/nacha/file_options.json</label>
              <textarea
                value={fileOptionsJson}
                onChange={e => { setFileOptionsJson(e.target.value); validateJson('fileOptions', e.target.value) }}
                style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85em', minHeight: 250 }}
              />
              {jsonErrors.fileOptions && <div style={{ color: '#dc3545', fontSize: '0.85em', marginTop: 4 }}>⚠️ Invalid JSON: {jsonErrors.fileOptions}</div>}
            </div>

            <div className="form-group">
              <label>📁 app/payment-gateway/nacha/vendor.json</label>
              <textarea
                value={vendorJson}
                onChange={e => { setVendorJson(e.target.value); validateJson('vendor', e.target.value) }}
                style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85em', minHeight: 300 }}
              />
              {jsonErrors.vendor && <div style={{ color: '#dc3545', fontSize: '0.85em', marginTop: 4 }}>⚠️ Invalid JSON: {jsonErrors.vendor}</div>}
            </div>

            <div className="form-group">
              <label>📁 app/template_vars/nachaPg.json</label>
              <textarea
                value={nachaPgJson}
                onChange={e => { setNachaPgJson(e.target.value); validateJson('nachaPg', e.target.value) }}
                style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85em', minHeight: 350 }}
              />
              {jsonErrors.nachaPg && <div style={{ color: '#dc3545', fontSize: '0.85em', marginTop: 4 }}>⚠️ Invalid JSON: {jsonErrors.nachaPg}</div>}
            </div>

            <h2 style={{ marginTop: 25 }}>🌍 Environment Files</h2>

            {hasSerenityprdpr ? (
              <div className="form-group">
                <label>📁 env/serenityprdpr.json <span style={{ color: '#28a745', fontSize: '0.85em' }}>(loaded from repo)</span></label>
                <textarea
                  value={serenityprdprJson}
                  onChange={e => { setSerenityprdprJson(e.target.value); validateJson('serenityprdpr', e.target.value) }}
                  style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85em', minHeight: 200 }}
                />
                {jsonErrors.serenityprdpr && <div style={{ color: '#dc3545', fontSize: '0.85em', marginTop: 4 }}>⚠️ Invalid JSON: {jsonErrors.serenityprdpr}</div>}
              </div>
            ) : (
              <div style={{ padding: '10px 15px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 6, color: '#856404', marginBottom: 15 }}>
                ℹ️ <code>env/serenityprdpr.json</code> not found in the repository.
              </div>
            )}

            {hasSerenityprod1 ? (
              <div className="form-group">
                <label>📁 env/serenityprod1.json <span style={{ color: '#28a745', fontSize: '0.85em' }}>(loaded from repo)</span></label>
                <textarea
                  value={serenityprod1Json}
                  onChange={e => { setSerenityprod1Json(e.target.value); validateJson('serenityprod1', e.target.value) }}
                  style={{ fontFamily: "'Courier New', monospace", fontSize: '0.85em', minHeight: 200 }}
                />
                {jsonErrors.serenityprod1 && <div style={{ color: '#dc3545', fontSize: '0.85em', marginTop: 4 }}>⚠️ Invalid JSON: {jsonErrors.serenityprod1}</div>}
              </div>
            ) : (
              <div style={{ padding: '10px 15px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 6, color: '#856404', marginBottom: 15 }}>
                ℹ️ <code>env/serenityprod1.json</code> not found in the repository.
              </div>
            )}

            <button className="btn btn-primary" disabled={runner.running} onClick={handleRun} style={{ marginTop: 15 }}>
              {runner.running ? '⏳ Running...' : '🚀 Commit & Create PR'}
            </button>
            {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} />}
            {runner.output && <ConsoleOutput content={runner.output} />}
          </>
        )}
      </div>
    </PageLayout>
  )
}
