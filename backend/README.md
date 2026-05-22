# Backend — 游戏素材生成服务

## 目录结构

```
backend/
├── main.py          # FastAPI 应用与路由
├── wanx_client.py   # 通义万相文生图封装
├── requirements.txt
├── .env.example     # 环境变量模板
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

## 3. 启动服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问 <http://localhost:8000/docs> 查看自动生成的 API 文档。

## 4. 接口说明

### POST /api/generate

**请求：**

```json
{ "prompt": "像素风格的勇者骑士，正面站立，游戏角色，白色背景" }
```

**成功响应（200）：**

```json
{ "image_url": "https://..." }
```

**错误响应（502）：**

```json
{ "detail": "任务 xxx 失败：..." }
```

### GET /health

返回 `{"status": "ok"}`，可用于健康检查。

## 5. 本地快速测试

```bash
# 方式一：curl
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "像素风勇者，游戏角色，白色背景"}'

# 方式二：浏览器打开 Swagger UI
# http://localhost:8000/docs
```
