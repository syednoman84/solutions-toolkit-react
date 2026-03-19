import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

interface Props {
  title: string
  subtitle: string
  icon?: string
  children: ReactNode
}

export default function PageLayout({ title, subtitle, icon, children }: Props) {
  return (
    <>
      <Link to="/" className="back-btn">← Back</Link>
      <div className="container">
        <div className="header">
          <h1>{icon} {title}</h1>
          <p>{subtitle}</p>
        </div>
        {children}
      </div>
    </>
  )
}
