interface Props {
  percent: number
  text: string
  variant?: 'primary' | 'danger'
}

export default function ProgressBar({ percent, text, variant = 'primary' }: Props) {
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div
          className={`progress-fill${variant === 'danger' ? ' danger' : ''}`}
          style={{ width: `${percent}%` }}
        >
          {percent}%
        </div>
      </div>
      <div className="progress-text">{text}</div>
    </div>
  )
}
