# Frontend — 游戏素材生成界面

## 安装依赖

```bash
cd frontend
npm install
```

## 启动开发服务器

```bash
npm run dev
```

默认访问地址：http://localhost:5173

> `/api` 请求会自动通过 Vite proxy 转发到后端 `http://localhost:8000`，无需手动处理跨域。

## 同时启动前后端（推荐）

开两个终端窗口：

**终端 1 — 后端**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**终端 2 — 前端**
```bash
cd frontend
npm run dev
```

然后在浏览器打开 http://localhost:5173 即可使用完整功能。
