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
  const [selected, setSelected] = useState(new Set())
  const [atlasFormat, setAtlasFormat] = useState('json')
  const [packing, setPacking] = useState(false)

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
    setSelected(prev => { const s = new Set(prev); s.delete(id); return s })
  }

  function toggleSelect(id) {
    setSelected(prev => {
      const s = new Set(prev)
      s.has(id) ? s.delete(id) : s.add(id)
      return s
    })
  }

  async function handlePack() {
    const localUrls = gallery
      .filter(item => selected.has(item.id) && item.imageUrl.startsWith('/static/'))
      .map(item => item.imageUrl)

    if (localUrls.length < 2) {
      setError('打包需要至少 2 张本地图片（外部 URL 不支持）')
      return
    }

    setPacking(true)
    setError('')
    try {
      const res = await fetch('/api/pack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_urls: localUrls, atlas_format: atlasFormat }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || `请求失败 (${res.status})`)
      }
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = 'sprites.zip'
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (err) {
      setError(err.message || '打包失败，请重试')
    } finally {
      setPacking(false)
    }
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

  const selectedLocalCount = gallery.filter(
    item => selected.has(item.id) && item.imageUrl.startsWith('/static/')
  ).length

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

        {selected.size >= 1 && (
          <div className="pack-bar">
            <span className="hint">
              已选 {selected.size} 张
              {selectedLocalCount < selected.size && `（${selectedLocalCount} 张可打包）`}
            </span>

            <div className="pack-format">
              <span className="selector-label">图集格式</span>
              <div className="selector-options">
                <button
                  className={`selector-btn${atlasFormat === 'json' ? ' active' : ''}`}
                  onClick={() => setAtlasFormat('json')}
                >
                  JSON
                </button>
                <button
                  className={`selector-btn${atlasFormat === 'godot' ? ' active' : ''}`}
                  onClick={() => setAtlasFormat('godot')}
                >
                  Godot
                </button>
              </div>
            </div>

            <button
              className="pack-btn"
              onClick={handlePack}
              disabled={packing || selectedLocalCount < 2}
              title={selectedLocalCount < 2 ? '至少需要 2 张本地图片' : ''}
            >
              {packing ? '打包中...' : '打包导出'}
            </button>
            <button className="pack-btn secondary" onClick={() => setSelected(new Set())}>
              取消选择
            </button>
          </div>
        )}

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
              <div
                key={item.id}
                className={`gallery-card${selected.has(item.id) ? ' selected' : ''}`}
              >
                <label className="card-select">
                  <input
                    type="checkbox"
                    checked={selected.has(item.id)}
                    onChange={() => toggleSelect(item.id)}
                  />
                </label>
                <div className="card-image" onClick={() => toggleSelect(item.id)}>
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
