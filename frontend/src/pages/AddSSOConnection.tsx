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
  { percent: 70, text: 'Updating queueManagerUISettings.json...' },
  { percent: 85, text: 'Committing and pushing changes...' },
  { percent: 99, text: 'Creating pull request...' },
]

export default function AddSSOConnection() {
  const [destRepo, setDestRepo] = useState('https://git.shared.linearft.tools/odx-platform-configs/ODXP-DPLOY--odx-config-tenantId-deploy.git')
  const [prTitle, setPrTitle] = useState('Adding SSO Connection')
  const [commitMessage, setCommitMessage] = useState('Adding SSO Connection')
  const [branchName, setBranchName] = useState('feature/SCS-XYZ-sso')
  const [displayName, setDisplayName] = useState('')
  const [connectionName, setConnectionName] = useState('')
  const [ssoUrl, setSsoUrl] = useState('')
  const runner = useProgressRunner()

  const handleRun = () => {
    if (!destRepo || !prTitle || !commitMessage || !branchName || !displayName || !connectionName || !ssoUrl) {
      alert('⚠️ All fields are required!'); return
    }
    runner.run(steps, () => api.ssoRun(), async () => {
      await api.ssoSaveParams({
        destRepo, prTitle, commitMessage, branchName,
        connections: [{ displayName, connectionName, ssoUrl }],
      })
    })
  }

  return (
    <PageLayout title="Add SSO Connection Configuration" subtitle="Add SSO connection to an existing tenant's queueManagerUISettings.json" icon="🔐">
      <div className="content">
        <h2>🔐 Add SSO Connection to Existing Tenant</h2>
        <div className="info-box">
          <strong>ℹ️ Info:</strong> This will update <code>app/template_vars/queueManagerUISettings.json</code> in the
          tenant config repo by adding entries to <code>FEATURE_CONNECTIONS</code> and
          <code>REACT_APP_IDP_AUTHORIZATION_URLS</code>. Duplicate entries are automatically skipped.
        </div>

        <div className="form-group"><label>📦 Destination Repository URL (Existing Tenant)</label>
          <input value={destRepo} onChange={e => setDestRepo(e.target.value)} /></div>
        <div className="form-group"><label>📝 Pull Request Title</label>
          <input value={prTitle} onChange={e => setPrTitle(e.target.value)} /></div>
        <div className="form-group"><label>💬 Commit Message</label>
          <input value={commitMessage} onChange={e => setCommitMessage(e.target.value)} /></div>
        <div className="form-group"><label>🌱 Branch Name</label>
          <input value={branchName} onChange={e => setBranchName(e.target.value)} /></div>

        <div className="form-group">
          <label>🔗 SSO Connection</label>
          <div className="connection-labels">
            <span>Display Name</span><span>Connection Name</span><span>SSO URL</span>
          </div>
          <div className="connection-row">
            <input placeholder="e.g. Velera Employee" value={displayName} onChange={e => setDisplayName(e.target.value)} />
            <input placeholder="e.g. SerProd1-vla-SAMLAD" value={connectionName} onChange={e => setConnectionName(e.target.value)} />
            <input placeholder="e.g. /oauth2/authorization/connection7" value={ssoUrl} onChange={e => setSsoUrl(e.target.value)} />
          </div>
        </div>

        <button className="btn btn-primary" disabled={runner.running} onClick={handleRun}>🔐 Add SSO Connection</button>
        {runner.progress && <ProgressBar percent={runner.progress.percent} text={runner.progress.text} />}
        {runner.output && <ConsoleOutput content={runner.output} />}
      </div>
    </PageLayout>
  )
}
