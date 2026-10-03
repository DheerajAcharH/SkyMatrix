import { Activity, ArrowUpRight, Crosshair, MapPin, Radio, RefreshCw, ShieldCheck } from 'lucide-react'
import { useDashboardViewModel } from '../viewmodels/useDashboardViewModel'

const timeFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export function DashboardView() {
  const dashboard = useDashboardViewModel()

  return (
    <main className="shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="SkyMatrix field monitor">
          <span className="brand-mark"><Crosshair size={19} strokeWidth={2.4} /></span>
          <span>SKYMATRIX<span className="brand-sub">FIELD MONITOR</span></span>
        </a>
        <div className="connection"><span className={`live-dot ${dashboard.error ? 'offline' : ''}`} /> {dashboard.error ? 'API UNAVAILABLE' : dashboard.loading ? 'CONNECTING' : 'SYSTEM ONLINE'} <span className="divider" /> INFERENCE API</div>
      </header>

      <section className="intro" id="top">
        <div>
          <p className="eyebrow">OPERATIONS / CAMERA NETWORK</p>
          <h1>Field overview</h1>
          <p className="subhead">Incoming frames, model detections, and device activity.</p>
        </div>
        <button className="refresh-button" onClick={() => void dashboard.refresh()} disabled={dashboard.loading} title="Refresh predictions">
          <RefreshCw size={16} className={dashboard.loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </section>

      <section className="metrics" aria-label="Prediction summary">
        <article className="metric metric-highlight">
          <div className="metric-heading"><span>Latest frame</span><Radio size={16} /></div>
          <strong>{dashboard.latest ? timeFormat.format(new Date(dashboard.latest.created_at)) : '--'}</strong>
          <small>{dashboard.latest ? dashboard.latest.device_id : 'Awaiting first upload'}</small>
        </article>
        <article className="metric">
          <div className="metric-heading"><span>Detections in view</span><Crosshair size={16} /></div>
          <strong>{dashboard.latest?.detection_count ?? '--'}</strong>
          <small>Latest processed image</small>
        </article>
        <article className="metric">
          <div className="metric-heading"><span>Frames recorded</span><Activity size={16} /></div>
          <strong>{dashboard.predictions.length}</strong>
          <small>{dashboard.totalDetections} detections in recent view</small>
        </article>
        <article className="metric">
          <div className="metric-heading"><span>Model confidence</span><ShieldCheck size={16} /></div>
          <strong>35<em>%</em></strong>
          <small>Person detection threshold</small>
        </article>
      </section>

      <section className="model-test" aria-labelledby="model-test-title">
        <div className="test-heading">
          <div><p className="eyebrow">MODEL CHECK</p><h2 id="model-test-title">Test an image</h2></div>
          <span className="update-label">JPEG or PNG / 10 MB max</span>
        </div>
        <div className="test-layout">
          <form className="test-form" onSubmit={(event) => { event.preventDefault(); void dashboard.runModelTest() }}>
            <label className="file-control">
              <span>Choose an image</span>
              <input type="file" accept="image/jpeg,image/png" onChange={(event) => dashboard.setTestFile(event.target.files?.[0] ?? null)} />
            </label>
            {dashboard.testFile && <span className="selected-file">{dashboard.testFile.name}</span>}
            <button className="test-button" type="submit" disabled={!dashboard.testFile || dashboard.testing}>
              <Crosshair size={16} /> {dashboard.testing ? 'Running inference...' : 'Run model test'}
            </button>
            <p className="test-footnote">The stored device key is used automatically for this test. Test images are not saved.</p>
            {dashboard.testError && <div className="notice" role="alert">{dashboard.testError}</div>}
          </form>
          <div className="test-output" aria-live="polite">
            {dashboard.testResult ? (
              <>
                <img className="annotated-preview" src={dashboard.testResult.annotated_image} alt="Model result with detected objects marked" />
                <div className="test-result-summary">
                  <strong>{dashboard.testResult.detections.length} {dashboard.testResult.detections.length === 1 ? 'detection' : 'detections'}</strong>
                  <div className="detection-tags">
                    {dashboard.testResult.detections.length ? dashboard.testResult.detections.map((item, index) => (
                      <span className="detection-tag" key={`${item.class_id}-${index}`}>{item.label}<b>{Math.round(item.confidence * 100)}%</b></span>
                    )) : <span className="no-detections">No objects above threshold</span>}
                  </div>
                </div>
              </>
            ) : (
              <div className="test-placeholder"><Crosshair size={21} /><span>{dashboard.testing ? 'Processing image...' : 'Annotated result will appear here'}</span></div>
            )}
          </div>
        </div>
      </section>

      <section className="feed-section">
        <div className="section-heading">
          <div><p className="eyebrow">LIVE FEED</p><h2>Recent predictions</h2></div>
          <span className="update-label">{dashboard.updatedAt ? `Updated ${dashboard.updatedAt.toLocaleTimeString()}` : 'Syncing'}</span>
        </div>

        {dashboard.error && <div className="notice" role="alert">{dashboard.error}</div>}
        {dashboard.loading && dashboard.predictions.length === 0 && <div className="empty-state">Connecting to prediction service...</div>}
        {!dashboard.loading && !dashboard.error && dashboard.predictions.length === 0 && (
          <div className="empty-state"><span className="empty-icon"><Radio size={20} /></span><strong>No frames received</strong><span>When the ESP32-CAM sends its first image, its marked prediction will appear here.</span></div>
        )}

        {dashboard.predictions.length > 0 && (
          <div className="prediction-list">
            {dashboard.predictions.map((prediction, index) => (
              <article className="prediction-row" key={prediction.id}>
                <div className="frame-thumb">
                  <img src={prediction.image_url} alt={`Annotated frame from ${prediction.device_id}`} loading={index < 3 ? 'eager' : 'lazy'} />
                  <a className="image-open" href={prediction.image_url} target="_blank" rel="noreferrer" title="Open annotated image"><ArrowUpRight size={14} /></a>
                </div>
                <div className="frame-main">
                  <div className="frame-title"><strong>{prediction.device_id}</strong><span className={prediction.detection_count ? 'count-pill active' : 'count-pill'}>{prediction.detection_count} {prediction.detection_count === 1 ? 'detection' : 'detections'}</span></div>
                  <div className="detection-tags">
                    {prediction.detections.length ? prediction.detections.slice(0, 5).map((item, itemIndex) => (
                      <span className="detection-tag" key={`${item.class_id}-${itemIndex}`}>{item.label}<b>{Math.round(item.confidence * 100)}%</b></span>
                    )) : <span className="no-detections">No objects above threshold</span>}
                    {prediction.detections.length > 5 && <span className="more-tag">+{prediction.detections.length - 5}</span>}
                  </div>
                  <span className="frame-location"><MapPin size={13} />{prediction.latitude != null && prediction.longitude != null ? `${prediction.latitude.toFixed(5)}, ${prediction.longitude.toFixed(5)}` : 'Location unavailable'}</span>
                </div>
                <time className="frame-time" dateTime={prediction.created_at}>{timeFormat.format(new Date(prediction.created_at))}</time>
              </article>
            ))}
          </div>
        )}
      </section>
      <footer><span>SKYMATRIX / YOLO INFERENCE</span><span>Annotated frames served from Cloudinary</span></footer>
    </main>
  )
}
