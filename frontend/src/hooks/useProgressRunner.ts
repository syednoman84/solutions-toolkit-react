import { useState, useRef, useCallback } from 'react'
import type { ProgressStep } from '../types'

export function useProgressRunner() {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState<{ percent: number; text: string } | null>(null)
  const [output, setOutput] = useState('')
  const intervalRef = useRef<ReturnType<typeof setInterval>>(null)

  const run = useCallback(async (
    steps: ProgressStep[],
    execute: () => Promise<{ stdout?: string; stderr?: string; returncode?: number; error?: string }>,
    onBefore?: () => Promise<void>,
  ) => {
    setRunning(true)
    setOutput('')
    let stepIdx = 0

    setProgress({ percent: steps[0].percent, text: steps[0].text })
    stepIdx = 1

    try {
      if (onBefore) await onBefore()

      intervalRef.current = setInterval(() => {
        if (stepIdx < steps.length) {
          setProgress({ percent: steps[stepIdx].percent, text: steps[stepIdx].text })
          stepIdx++
        }
      }, 2000)

      const result = await execute()
      if (intervalRef.current) clearInterval(intervalRef.current)

      setProgress({ percent: 100, text: 'Completed!' })

      await new Promise(r => setTimeout(r, 800))
      setProgress(null)

      if (result.error) {
        setOutput(`❌ Error: ${result.error}`)
        return false
      }

      let out = result.stdout || ''
      if (result.returncode !== 0 && result.stderr) {
        out += '\n\n❌ Errors:\n' + result.stderr
      }
      setOutput(out)
      return result.returncode === 0
    } catch (err: unknown) {
      if (intervalRef.current) clearInterval(intervalRef.current)
      setProgress(null)
      setOutput(`❌ Error: ${err instanceof Error ? err.message : String(err)}`)
      return false
    } finally {
      setRunning(false)
    }
  }, [])

  return { running, progress, output, run }
}
