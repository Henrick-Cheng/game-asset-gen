import { useEffect, useState } from 'react'
import './App.css'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('pixel-art')
  const [assetType, setAssetType] = useState('character')
  const [removeBg, setRemoveBg] = useState(true)
  const [styles, setStyles] = useState([])
  const [assetTypes, setAssetTypes] = useState([])
  const [gallery, setGallery] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch('/api/styles').then(r => r.json()).then(setStyles).catch(() => {})
    fetch('/api/asset-types').then(r => r.json()).then(setAssetTypes).catch(() => {})
  }, [])

  async function handleGenerate() {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), style, asset_type: assetType, remove_bg: removeBg }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || `请求失败 (${res.status})`)

      const styleName = styles.find(s => s.id === style)?.name ?? style
      const assetTypeName = assetTypes.find(t => t.id === assetType)?.name ?? assetType

      setGallery(prev => [{
        id: Date.now(),
        imageUrl: data.image_url,
        prompt: prompt.trim(),
        styleName,
        assetTypeName,
      }, ...prev])
    } catch (err) {
      setError(err.message || '生成失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !loading) handleGenerate()
  }

  function handleDelete(id) {
    setGallery(prev => prev.filter(item => item.id !== id))
  }

  async function handleDownload(imageUrl, prompt) {
    try {
      const res = await fetch(imageUrl)
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${prompt.slice(0, 20).replace(/[\s/\\:*?"<>|]+/g, '_')}.png`
      a.click()
      URL.revokeObjectURL(a.href)
    } catch {
      window.open(imageUrl, '_blank')
    }
  }

  return (
    <div className="app">
      <div className="controls">
        <h1>2D 游戏素材生成</h1>

        <div className="input-row">
          <input
            type="text"
            placeholder="描述你想要的游戏素材，例如：像素风勇者骑士，正面站立"
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button onClick={handleGenerate} disabled={loading || !prompt.trim()}>
            {loading ? '生成中...' : '生成'}
          </button>
        </div>

        <div className="selector-row">
          <div className="selector-group">
            <span className="selector-label">素材类型</span>
            <div className="selector-options">
              {assetTypes.map(t => (
                <button
                  key={t.id}
                  className={`selector-btn${assetType === t.id ? ' active' : ''}`}
                  onClick={() => setAssetType(t.id)}
                  disabled={loading}
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>

          <div className="selector-group">
            <span className="selector-label">风格</span>
            <div className="selector-options">
              {styles.map(s => (
                <button
                  key={s.id}
                  className={`selector-btn${style === s.id ? ' active' : ''}`}
                  onClick={() => setStyle(s.id)}
                  disabled={loading}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          <label className="toggle-row">
            <input
              type="checkbox"
              checked={removeBg}
              onChange={e => setRemoveBg(e.target.checked)}
              disabled={loading}
            />
            去除背景
          </label>
        </div>

        {error && <p className="error">{error}</p>}
        {loading && <p className="hint">正在生成，通常需要 10～30 秒...</p>}
      </div>

      <main className="gallery-section">
        {gallery.length === 0 ? (
          <div className="gallery-empty">
            <p className="hint">生成的素材将在这里以画廊形式展示</p>
          </div>
        ) : (
          <div className="gallery-grid">
            {gallery.map(item => (
              <div key={item.id} className="gallery-card">
                <div className="card-image">
                  <img src={item.imageUrl} alt={item.prompt} />
                </div>
                <div className="card-meta">
                  <p className="card-prompt">{item.prompt}</p>
                  <p className="card-tags">
                    <span className="tag">{item.styleName}</span>
                    <span className="tag">{item.assetTypeName}</span>
                  </p>
                </div>
                <div className="card-actions">
                  <button className="card-btn" onClick={() => handleDownload(item.imageUrl, item.prompt)}>
                    下载
                  </button>
                  <button className="card-btn danger" onClick={() => handleDelete(item.id)}>
                    删除
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
