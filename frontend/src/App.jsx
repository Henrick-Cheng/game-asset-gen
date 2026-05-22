import { useState } from 'react'
import './App.css'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleGenerate() {
    if (!prompt.trim()) return
    setLoading(true)
    setError('')
    setImageUrl('')

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
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
