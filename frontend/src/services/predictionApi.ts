import type { Detection, Prediction } from '../models/prediction'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? 'https://skymatrix.onrender.com').replace(/\/$/, '')

export type InferenceTestResult = {
  detections: Detection[]
  annotated_image: string
}

export async function getPredictions(signal?: AbortSignal): Promise<Prediction[]> {
  if (!apiBaseUrl) throw new Error('The prediction API URL is not configured.')

  const response = await fetch(`${apiBaseUrl}/api/v1/predictions?limit=50`, { signal })
  if (!response.ok) throw new Error(`Prediction service returned ${response.status}.`)
  const data: { items: Prediction[] } = await response.json()
  return data.items
}

export async function testPrediction(image: File, deviceKey: string): Promise<InferenceTestResult> {
  if (!apiBaseUrl) throw new Error('The prediction API URL is not configured.')

  const form = new FormData()
  form.append('image', image)
  const response = await fetch(`${apiBaseUrl}/api/v1/predictions/test`, {
    method: 'POST',
    headers: { 'X-Device-Key': deviceKey },
    body: form,
  })
  const data = await response.json()
  if (!response.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : `Prediction service returned ${response.status}.`)
  }
  return data as InferenceTestResult
}
