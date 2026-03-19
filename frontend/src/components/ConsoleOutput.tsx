interface Props {
  content: string
  dark?: boolean
}

export default function ConsoleOutput({ content, dark }: Props) {
  if (!content) return null
  return (
    <>
      <h3 style={{ marginTop: 30, marginBottom: 10, color: '#495057' }}>📋 Console Log</h3>
      <div className={dark ? 'output-dark' : 'output'}>{content}</div>
    </>
  )
}
