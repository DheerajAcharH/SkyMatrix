export type Detection = {
  class_id: number
  label: string
  confidence: number
  box: [number, number, number, number]
}

export type Prediction = {
  id: string
  created_at: string
  detection_count: number
  detections: Detection[]
  image_url: string
  latitude: number | null
  longitude: number | null
  device_id: string
}
