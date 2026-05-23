# 开发进度记录

## 2026-05-23

### 完成功能
- 后端骨架与通义万相文生图接口
- 前端最小界面与前后端联调

### 改动的主要文件
- `backend/main.py` — FastAPI 应用，`POST /api/generate`、`GET /health`
- `backend/wanx_client.py` — 通义万相异步任务封装（提交 + 轮询）
- `backend/requirements.txt` — 后端依赖
- `backend/.env.example` — 环境变量模板
- `frontend/src/App.jsx` — 单页面组件，输入框 + 生成按钮 + 图片展示
- `frontend/src/App.css` — 界面样式
- `frontend/vite.config.js` — Vite proxy 配置（`/api` → `localhost:8000`）
- `CLAUDE.md` — 项目说明、协作规范、每日收尾规则

### 技术实现要点
- 通义万相文生图为异步接口：先 POST 提交任务拿 `task_id`，再 GET 轮询状态，每 2 秒一次，超时 120 秒
- HTTP 4xx/5xx 错误统一包成 `WanxError`，路由层捕获后返回 502，避免漏成 500
- Vite proxy 转发 `/api` 请求解决开发环境跨域
- Node.js 版本限制（当前 20.13.1），锁定 Vite 5.x

---

## 2026-05-24

### 完成功能
- 后端提示词处理管线：Qwen 增强 + 风格预设
- 新增 `GET /api/styles` 接口，返回所有可用风格预设列表

### 改动的主要文件
- `backend/style_presets.py` — 新建，3 种风格预设配置（pixel-art / flat-vector / hand-drawn）
- `backend/prompt_enhancer.py` — 新建，调用 qwen-plus 扩写提示词，失败时自动降级返回原始 prompt
- `backend/main.py` — `GenerateRequest` 新增 `style` 字段，generate 改为三步管线，新增 `/api/styles` 路由
- `backend/README.md` — 更新接口文档与本地测试命令

### 技术实现要点
- 生成管线顺序：用户 prompt → Qwen 增强（qwen-plus）→ 拼接风格后缀 → 通义万相文生图
- Qwen 使用 DashScope OpenAI 兼容接口（`/compatible-mode/v1/chat/completions`），复用 `DASHSCOPE_API_KEY`
- Qwen 任何异常（网络、超时、API 错误）均捕获并降级，不影响主流程
- `style` 字段默认值 `"pixel-art"`，传入非法值返回 422

### 本地测试验证步骤
```bash
# 1. 启动后端
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000

# 2. 验证 /api/styles（浏览器或 curl）
curl http://localhost:8000/api/styles
# 期望：[{"id":"pixel-art","name":"像素风"},{"id":"flat-vector","name":"扁平矢量"},{"id":"hand-drawn","name":"手绘卡通"}]

# 3. 验证 /api/generate 出图（三种 style 各测一次）
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "勇者骑士，正面站立，白色背景", "style": "pixel-art"}'

curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "宝剑道具图标，白色背景", "style": "flat-vector"}'

curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "可爱小猫咪角色，白色背景", "style": "hand-drawn"}'

# 4. 验证非法 style 返回 422
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试", "style": "invalid"}'
```
