import { useEffect, useState } from 'react'
import './App.css'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState('pixel-art')
  const [assetType, setAssetType] = useState('character')
  const [styles, setStyles] = useState([])
  const [assetTypes, setAssetTypes] = useState([])
  const [imageUrl, setImageUrl] = useState('')
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
    setImageUrl('')

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim(), style, asset_type: assetType }),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || `请求失败 (${res.status})`)
      }
      setImageUrl(data.image_url)
    } catch (err) {
      setError(err.message || '生成失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !loading) handleGenerate()
  }

  return (
    <div className="container">
      <h1>2D 游戏素材生成</h1>

      <div className="input-row">
        <input
          type="text"
          placeholder="描述你想要的游戏素材，例如：像素风勇者骑士，正面站立，白色背景"
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
      </div>

      {error && <p className="error">{error}</p>}

      <div className="image-area">
        {loading && <p className="hint">正在生成，通常需要 10～30 秒...</p>}
        {imageUrl && <img src={imageUrl} alt="生成结果" />}
        {!loading && !imageUrl && !error && (
          <p className="hint">图片将显示在这里</p>
        )}
      </div>
    </div>
  )
}
