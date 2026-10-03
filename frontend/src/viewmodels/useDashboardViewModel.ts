import { useEffect, useState } from 'react'
import type { Prediction } from '../models/prediction'
import { getPredictions, testPrediction, type InferenceTestResult } from '../services/predictionApi'

export function useDashboardViewModel() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const [testFile, setTestFile] = useState<File | null>(null)
  const [deviceKey, setDeviceKey] = useState('')
  const [testResult, setTestResult] = useState<InferenceTestResult | null>(null)
  const [testError, setTestError] = useState<string | null>(null)
  const [testing, setTesting] = useState(false)

  async function refresh(signal?: AbortSignal) {
    setError(null)
    try {
      const rows = await getPredictions(signal)
      setPredictions(rows)
      setUpdatedAt(new Date())
    } catch (cause) {
      if (cause instanceof Error && cause.name === 'AbortError') return
      setError(cause instanceof Error ? cause.message : 'Unable to load prediction history.')
    } finally {
      if (!signal?.aborted) setLoading(false)
    }
  }

  useEffect(() => {
    const controller = new AbortController()
    void refresh(controller.signal)
    const timer = window.setInterval(() => void refresh(), 15_000)
    return () => {
      controller.abort()
      window.clearInterval(timer)
    }
  }, [])

  const totalDetections = predictions.reduce((sum, item) => sum + item.detection_count, 0)
  const latest = predictions[0] ?? null

  async function runModelTest() {
    if (!testFile || !deviceKey) return
    setTesting(true)
    setTestError(null)
    setTestResult(null)
    try {
      setTestResult(await testPrediction(testFile, deviceKey))
    } catch (cause) {
      setTestError(cause instanceof Error ? cause.message : 'Model test failed.')
    } finally {
      setTesting(false)
    }
  }

  return {
    predictions, loading, error, updatedAt, latest, totalDetections, refresh,
    testFile, setTestFile, deviceKey, setDeviceKey, testResult, testError, testing, runModelTest,
  }
}
