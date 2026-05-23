# Backend — 游戏素材生成服务

## 目录结构

```
backend/
├── main.py              # FastAPI 应用与路由
├── wanx_client.py       # 通义万相文生图封装
├── prompt_enhancer.py   # Qwen 提示词增强（失败时自动降级）
├── style_presets.py     # 风格预设配置
├── asset_types.py       # 素材类型配置
├── requirements.txt
├── .env.example         # 环境变量模板
└── README.md
```

## 1. 安装依赖

建议使用虚拟环境：

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的阿里云 DashScope API Key
```

Key 获取地址：<https://dashscope.console.aliyun.com/apiKey>

`DASHSCOPE_API_KEY` 同时用于通义万相和 Qwen，只需配置一次。

## 3. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问 <http://localhost:8000/docs> 查看自动生成的 API 文档。

## 4. 接口说明

### POST /api/generate

处理流程：用户 prompt → Qwen 增强 → 拼接风格后缀 → 拼接类型提示词 → 通义万相文生图

**请求：**

```json
{
  "prompt": "像素风格的勇者骑士，正面站立，白色背景",
  "style": "pixel-art",
  "asset_type": "character"
}
```

`style` 可选，默认 `"pixel-art"`，可选值见 `/api/styles`。
`asset_type` 可选，默认 `"character"`，可选值见 `/api/asset-types`。

**成功响应（200）：**

```json
{ "image_url": "https://..." }
```

**错误响应（422）：** `style` 传了不存在的值

**错误响应（502）：** 通义万相调用失败

---

### GET /api/asset-types

返回所有可用素材类型列表。

**响应示例：**

```json
[
  { "id": "character", "name": "角色精灵" },
  { "id": "icon",      "name": "道具图标" },
  { "id": "tile",      "name": "地块贴图" }
]
```

---

### GET /api/styles

返回所有可用风格预设列表。

**响应示例：**

```json
[
  { "id": "pixel-art",    "name": "像素风" },
  { "id": "flat-vector",  "name": "扁平矢量" },
  { "id": "hand-drawn",   "name": "手绘卡通" }
]
```

---

### GET /health

返回 `{"status": "ok"}`，可用于健康检查。

## 5. 本地测试

### 验证 /api/styles

```bash
curl http://localhost:8000/api/styles
```

期望输出：

```json
[{"id":"pixel-art","name":"像素风"},{"id":"flat-vector","name":"扁平矢量"},{"id":"hand-drawn","name":"手绘卡通"}]
```

### 验证 /api/generate（带不同 style）

```bash
# 像素风（默认）
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "像素风勇者骑士，正面站立，白色背景", "style": "pixel-art"}'

# 扁平矢量
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "宝剑道具图标，白色背景", "style": "flat-vector"}'

# 手绘卡通
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "可爱小猫咪角色，白色背景", "style": "hand-drawn"}'
```

成功时响应中包含 `"image_url": "https://..."` 图片链接。

### 验证 style 校验

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "测试", "style": "invalid-style"}'
```

期望返回 `422 Unprocessable Entity`。

### 浏览器 Swagger UI

访问 <http://localhost:8000/docs>，可交互式测试所有接口。
