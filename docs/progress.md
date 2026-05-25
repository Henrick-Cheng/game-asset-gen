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

---

## 2026-05-24（续）

### 完成功能
- 素材类型区分（character / icon / tile），与风格预设正交组合
- 新增 `GET /api/asset-types` 接口
- 前端新增素材类型与风格两组选择器

### 改动的主要文件
- `backend/asset_types.py` — 新建，3 种素材类型配置（character / icon / tile）
- `backend/main.py` — 新增 `asset_type` 字段与校验，pipeline 末尾拼接类型后缀，新增 `/api/asset-types` 路由
- `frontend/src/App.jsx` — 启动时拉取 `/api/styles` 和 `/api/asset-types`，新增两组胶囊选择器，生成时传 `asset_type`
- `frontend/src/App.css` — 新增 selector 相关样式
- `backend/README.md` — 更新目录结构与接口文档

### 技术实现要点
- 最终 prompt 拼接顺序：Qwen 增强结果 + 风格后缀 + 类型后缀
- 类型后缀描述构图/视角特征（全身居中 / 单物体图标 / 可平铺纹理），与风格后缀描述画面渲染风格，两者正交不干扰
- `asset_type` 字段默认值 `"character"`，非法值返回 422
- 并发测试时触发 DashScope 429 限流，顺序补跑可绕过

### 测试验证
- 固定 pixel-art，换三种类型出图：构图差异符合预期（全身角色 / 单物体图标 / 均匀纹理）
- 固定 character，换三种风格出图：像素/矢量/手绘视觉差异明显，类型特征保持一致
- 非法 `style` / `asset_type` / 空 prompt 均返回 422

---

## 2026-05-24（续二）

### 完成功能
- 去背景透明化：生成后可选用 rembg 本地抠图，输出透明 PNG
- 前端新增「去除背景」勾选框，默认勾选

### 改动的主要文件
- `backend/bg_remover.py` — 新建，下载万相图片 → rembg 去背景 → 存 `backend/static/{uuid}.png` → 返回 `/static/xxx.png`，失败降级返回原图
- `backend/main.py` — 挂载 `/static` 静态文件服务，`GenerateRequest` 新增 `remove_bg: bool = True` 字段，pipeline 末尾加去背景步骤
- `backend/requirements.txt` — 新增 `rembg==2.0.62`、`onnxruntime==1.26.0`
- `frontend/vite.config.js` — 开发代理新增 `/static → localhost:8000`
- `frontend/src/App.jsx` — 新增 `removeBg` 状态和勾选框，默认勾选，生成时传 `remove_bg`
- `frontend/src/App.css` — 新增 `.toggle-row` 勾选框样式
- `.gitignore` — 新增 `backend/static/`
- `backend/README.md` — 新增 rembg 首次下载说明、`remove_bg` 参数说明

### 技术实现要点
- 处理后图片保存在 `backend/static/`，通过 FastAPI `StaticFiles` 挂载为 `/static`，Vite dev proxy 同步转发
- `remove_bg=true` 返回 `/static/uuid.png`（RGBA 透明 PNG）；`remove_bg=false` 直接返回万相 HTTPS URL
- rembg 首次调用自动下载 u2net 模型（约 170 MB）到 `~/.u2net/`，后续直接用缓存
- 去背景任何异常均 catch 降级，不影响主流程
- `backend/static/` 不纳入版本控制

### 测试验证
- `remove_bg=false`：返回万相原图 HTTPS URL，状态 200 ✓
- `remove_bg=true`：返回 `/static/xxx.png`，文件 RGBA 模式，1024×1024，约 49% 像素透明 ✓
- `/static/xxx.png` HTTP 访问：200，Content-Type: image/png ✓

---

## 2026-05-25

### 完成功能
- 画廊式结果展示界面：每次生成结果累积为卡片，支持下载和删除

### 改动的主要文件
- `frontend/src/App.jsx` — 移除单张展示逻辑，改为 gallery 数组 state；每次生成成功后 prepend 新卡片；新增 handleDelete / handleDownload
- `frontend/src/App.css` — 整体重写布局：controls 固定顶部面板，gallery-section 占剩余区域；新增 gallery-grid、gallery-card、card-image（棋盘格）、card-meta、card-actions 等样式

### 技术实现要点
- 画廊数据存 React state（数组），刷新页面清空，无后端持久化
- 新生成的卡片 prepend（`[newCard, ...prev]`），最新结果排最前
- 每张卡片记录生成时的 prompt、styleName、assetTypeName，标注固定不随后续选择变化
- 棋盘格底纹用 4 段 CSS `linear-gradient` 实现，透明区域可直观显示
- 下载：先 fetch 转 Blob 创建 ObjectURL 触发下载，CORS 失败时降级 `window.open`
- 文件名取 prompt 前 20 字符，替换非法字符后加 `.png` 后缀

### 测试验证（Playwright 自动化）
- 连续生成 4 张（4 种风格/类型组合），画廊累积计数 1→2→3→4，无覆盖 ✓
- 每张卡片 prompt / 风格标签 / 类型标签与生成时选项一一匹配 ✓
- 下载触发 download 事件，文件名含 prompt 文字 ✓
- 删除中间某张，剩余 3 张内容正确 ✓
- 棋盘格底纹 CSS 生效，透明素材可视 ✓

---

## 2026-05-25（续）

### 完成功能
- 精灵图打包与引擎导出：从画廊多选素材，打包为精灵图大图 + 图集描述文件，以 ZIP 下载
- README.md 起草

### 改动的主要文件
- `backend/packer.py` — 新建，Shelf 行装箱算法 + JSON 图集生成 + Godot 4 `.tres` 图集生成 + ZIP 打包
- `backend/main.py` — 新增 `POST /api/pack` 接口，接收本地图片 URL 列表和格式参数，返回 ZIP
- `backend/requirements.txt` — 新增 `Pillow==12.2.0`（显式声明，rembg 已有此传递依赖）
- `backend/test_packer.py` — 新建，合成测试精灵图后验证不重叠、透明保留、坐标像素级对应；含 HTTP 接口端到端测试
- `frontend/src/App.jsx` — 新增 selected（Set）、atlasFormat、packing 状态；卡片复选框与点击图片区域可切换选中；选中 ≥1 张时显示打包栏；调用 `/api/pack` 后触发 ZIP 下载
- `frontend/src/App.css` — 新增打包栏（`.pack-bar`）、格式选择器（`.pack-format`）、打包按钮（`.pack-btn`）、卡片选中高亮（`.gallery-card.selected`、`.card-select`）样式
- `README.md` — 新建，含项目简介、核心功能、技术栈与依赖（区分第三方与原创）、目录结构、安装运行步骤

### 技术实现要点
- **Shelf 行装箱算法**：按高度降序排列，逐行从左到右放置；目标宽度取 `max(最宽图片宽, √总面积 × 1.2)`，上限 4096px；相邻精灵间留 1px 间距防纹理渗色
- **JSON 图集格式**：`{ frames: [{name, x, y, w, h}], meta: {image, size} }`，与 Phaser 3 / PixiJS 兼容
- **Godot 4 `.tres` 格式**：每帧生成独立 `[sub_resource type="AtlasTexture"]`，引用同目录 `res://spritesheet.png`，可直接在 Sprite2D 节点中引用
- **ZIP 返回**：FastAPI `Response(content=zip_bytes, media_type="application/zip")`，前端 `res.blob()` 后创建 ObjectURL 触发下载
- **输入校验**：URL 必须以 `/static/` 开头且文件存在（400/404）；图片数量 < 2 返回 422；atlas_format 非法返回 422

### 测试验证
- 合成 4 张不同尺寸测试精灵（64×80、32×32、128×24、40×56），逐帧验证中心像素有内容、四角 alpha=0（透明保留）✓
- 所有帧 AABB 两两不相交（无重叠）✓
- `meta.size` 与实际大图像素尺寸一致 ✓
- Godot `.tres` 中 AtlasTexture 数量与帧数一致，抽样坐标字符串出现在文件中 ✓
- 用真实 app 生成图（1024×1024）打包，坐标合法、有内容 ✓
- HTTP 接口端到端：正常请求返回 ZIP（200）；< 2 张返回 422；外部 URL 返回 400；文件不存在返回 404 ✓
