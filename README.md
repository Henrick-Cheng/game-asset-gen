# 2D 游戏素材生成工具

> 输入一句话描述，自动生成带透明背景的 2D 游戏素材，并可打包为引擎可直接导入的精灵图与图集文件。

---

## Demo 视频

https://www.bilibili.com/video/BV1KHGo6BEhG/


---

## 核心功能

| 功能 | 说明 |
|------|------|
| **文本生成素材** | 输入中文描述，经 Qwen 提示词增强后调用通义万相生成图片 |
| **风格预设** | 像素风 / 扁平矢量 / 手绘卡通，三种风格一键切换 |
| **素材类型区分** | 角色精灵 / 道具图标 / 地块贴图，针对不同类型优化构图提示词 |
| **去背景透明化** | 本地运行 rembg（U²-Net 模型）自动抠图，输出 RGBA 透明 PNG |
| **画廊管理** | 生成结果累积展示为卡片，支持单张下载和删除 |
| **精灵图打包导出** | 从画廊多选素材，一键打包为精灵图大图 + 图集描述文件，以 ZIP 下载 |
| **多引擎图集格式** | 支持 JSON 格式（Phaser 3 / PixiJS）和 Godot 4 `.tres` 格式 |

---

## 技术栈与第三方依赖

### 前端

| 库 / 工具 | 版本 | 用途 |
|-----------|------|------|
| React | 19 | UI 框架 |
| Vite | 5 | 构建工具，开发环境代理 `/api` 和 `/static` 到后端 |

> 前端无其他第三方 UI 库，组件与样式均为本项目原创实现。

### 后端

| 库 / 工具 | 版本 | 用途 |
|-----------|------|------|
| FastAPI | 0.115 | Web 框架，提供 REST API |
| Uvicorn | 0.32 | ASGI 服务器 |
| Pydantic | 2.10 | 请求体校验 |
| httpx | 0.27 | 异步 HTTP 客户端（调用 DashScope API）|
| python-dotenv | 1.0 | 读取 `.env` 环境变量 |
| rembg | 2.0.62 | 本地去背景（U²-Net 深度学习模型）|
| onnxruntime | 1.26 | rembg 的 ONNX 模型推理后端 |
| Pillow | 12.2 | 精灵图合成（图片读写、拼接、透明通道处理）|

### 第三方 AI 服务（阿里云 DashScope）

| 服务 | 模型 | 用途 |
|------|------|------|
| 通义万相 | `wanx2.1-t2i-turbo` | 文生图，生成游戏素材 |
| 通义千问 | `qwen-plus` | 提示词增强，将用户中文描述扩写为详细英文 prompt |

> 两个服务共用同一个 `DASHSCOPE_API_KEY`。

### 本项目原创实现的功能

以下功能**不依赖第三方库**，为本项目自行设计与编码：

- **三段式提示词管线**（`prompt_enhancer.py` + `style_presets.py` + `asset_types.py`）：用户描述 → Qwen 英文扩写 → 拼接风格后缀 → 拼接类型后缀，三层正交叠加
- **风格预设系统**：为像素风、扁平矢量、手绘卡通各自设计针对文生图的英文 prompt 后缀
- **素材类型系统**：为角色精灵、道具图标、地块贴图各自设计构图约束后缀，与风格预设两两正交组合（共 9 种组合）
- **Shelf 行装箱算法**（`packer.py`）：按高度降序排列素材、逐行紧凑放置，相比均匀网格更省面积
- **JSON 图集生成**：输出 Phaser 3 / PixiJS 兼容的 `frames` 数组格式，含 `meta.size` 元数据
- **Godot 4 `.tres` 图集生成**：为每帧生成独立 `AtlasTexture` sub-resource，可直接放入 Godot 项目引用
- **去背景降级策略**：rembg 任何异常均静默降级返回原图 URL，主流程不中断
- **画廊式累积展示**：纯 React state 管理，棋盘格底纹用纯 CSS `linear-gradient` 实现，直观显示透明区域

---

## 项目结构

```
game-asset-gen/
├── frontend/               # React + Vite 前端
│   ├── src/
│   │   ├── App.jsx         # 主页面：生成控制、画廊、打包导出
│   │   └── App.css         # 全部样式
│   ├── vite.config.js      # 开发代理配置
│   └── package.json
│
├── backend/                # Python + FastAPI 后端
│   ├── main.py             # 路由层：/api/generate /api/pack /api/styles /api/asset-types
│   ├── wanx_client.py      # 通义万相异步任务封装（提交 + 轮询）
│   ├── prompt_enhancer.py  # Qwen 提示词增强（失败自动降级）
│   ├── style_presets.py    # 风格预设配置
│   ├── asset_types.py      # 素材类型配置
│   ├── bg_remover.py       # rembg 去背景，结果存 static/
│   ├── packer.py           # 精灵图打包：Shelf 算法 + JSON/Godot 图集生成
│   ├── test_packer.py      # 打包模块单元测试（含像素级坐标验证）
│   ├── requirements.txt
│   ├── .env.example        # 环境变量模板
│   └── static/             # 运行时生成的图片（不纳入版本控制）
│
└── docs/
    └── progress.md         # 每日开发进度记录
```

---

## 安装与运行

### 前置条件

- Python 3.11+
- Node.js 18+
- 阿里云 DashScope API Key（在 [DashScope 控制台](https://dashscope.console.aliyun.com/) 申请，通义万相和 Qwen 共用同一个 Key）

### 1. 后端

```bash
cd backend

# 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置 API Key
cp .env.example .env
# 用编辑器打开 .env，将 DASHSCOPE_API_KEY=sk-xxx 替换为你的真实 Key

# 启动后端（默认监听 http://localhost:8000）
uvicorn main:app --reload
```

> **注意**：首次调用去背景功能时，rembg 会自动下载 U²-Net 模型（约 170 MB）到 `~/.u2net/`，之后直接使用缓存，无需重复下载。

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev
```

打开浏览器访问 `http://localhost:5173` 即可使用。前端通过 Vite 代理将 `/api` 和 `/static` 请求自动转发到后端，无需额外配置跨域。

### 3. 快速验证

后端启动后可用 curl 确认各接口正常：

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl http://localhost:8000/api/styles
# [{"id":"pixel-art","name":"像素风"},{"id":"flat-vector","name":"扁平矢量"},{"id":"hand-drawn","name":"手绘卡通"}]

curl http://localhost:8000/api/asset-types
# [{"id":"character","name":"角色精灵"},{"id":"icon","name":"道具图标"},{"id":"tile","name":"地块贴图"}]
```

---

## 设计思路与创新点

### 我们理解的真实需求

2D 游戏开发者对素材的需求和普通"找张好看的图"有本质差异：图片要有透明背景才能叠层；角色、道具、地块必须风格一致才能放进同一个场景；散图无法直接用，还需要打成精灵图并配图集描述文件，引擎才能按坐标索引每一帧。

换句话说，开发者缺的不是"生成图片的能力"，缺的是**从一句描述直通引擎可用素材的完整链路**。现有文生图工具止步于出图，剩下的抠图、拼图、写描述文件都要手工完成。我们把这条链路打通，是整个项目设计的出发点。

### 关键设计决策

**① 风格 × 类型两个正交维度，保证成套一致**

风格一致性靠的不是每次祈祷模型发挥稳定，而是系统设计：用户选定一种风格（pixel-art / flat-vector / hand-drawn）后，该风格的提示词后缀会附加到每一次生成请求，所有素材共享同一段画风描述，自然形成一套。

素材类型（角色精灵 / 道具图标 / 地块贴图）则是独立的第二维度，管的是构图和用途约束——地块需要平铺连续、图标需要主体居中、角色需要全身可见——这些与画风无关，单独管理才能和风格自由组合，产生 3×3 共 9 种有效组合，而不是风格和用途互相干扰。

**② Qwen 提示词增强，把"易用"和"质量"同时兜住**

文生图对提示词质量非常敏感，但要求用户写详细英文 prompt 会直接劝退大多数人。我们在用户输入和文生图接口之间插入一层 Qwen 调用：用户只需用中文写几个字，Qwen 负责理解意图、补充细节、翻译为英文，再拼接风格和类型后缀，最终送给通义万相。这一层让"一句话描述"和"稳定出图质量"同时成立。

**③ 精灵图打包 + 引擎 atlas 导出，把工具从"出图"延伸到"可用"**

这是我们认为最核心的差异点。画廊里的素材多选后，后端用 Shelf 行装箱算法（按高度降序排列、逐行紧凑放置，比均匀网格节省约 20–40% 面积）合成一张精灵图大图，同时生成两种图集描述文件：JSON 格式（Phaser 3 / PixiJS 的 `scene.load.atlas()` 可直接加载）和 Godot 4 `.tres` 格式（每帧对应一个 AtlasTexture sub-resource，拖进 Inspector 即用）。整包以 ZIP 下载，解压后直接放入引擎项目目录，不需要任何手工处理。

### 工程取舍

**去背景用本地 rembg 而非付费 API**：rembg 基于 U²-Net 在本地推理，零接口成本，也不把用户素材发往第三方服务。代价是首次运行要下载约 170 MB 的模型权重，以及 CPU 推理比 GPU 慢——对 72 h 比赛 demo 来说是可接受的。

**Qwen 失败时静默降级而非报错**：提示词增强是锦上添花，不是核心流程。Qwen 调用超时或异常时，直接把用户原始输入送给文生图，主流程继续，不因增强层的不稳定影响核心生成体验。

**画廊用前端 state 不做数据库**：持久化对比赛 demo 不是核心价值，把时间留给生成链路和导出格式。当前设计够演示完整工作流，没有过度工程。

### 局限与下一步

当前精灵图只支持静态帧，动画帧序列和帧间隔元数据尚未实现；引擎格式也只覆盖了 Godot 和 Phaser，Unity SpriteAtlas 等格式如果有更多时间可以补充。
