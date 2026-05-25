# 项目说明:2D 游戏素材生成工具

## 项目简介
这是一个比赛项目。Web 工具,用户输入文本描述和参数,生成可用于
2D 游戏开发的素材(角色精灵、道具图标、地块贴图等),并能导出为
主流 2D 引擎可直接使用的格式。

## 技术栈
- 前端:React + Vite (JavaScript)
- 后端:Python + FastAPI
- 文生图:阿里云 DashScope 通义万相
- 提示词增强:阿里云 DashScope Qwen 文本模型
- 去背景:rembg

## 目录结构
- frontend/  前端应用
- backend/   后端服务
- docs/      文档与 demo 视频链接

## 接口约定
- POST /api/generate  生成素材
- GET  /api/styles    获取风格预设列表
- GET  /api/asset-types 获取素材类型列表
- POST /api/pack      精灵图打包（返回 ZIP）

## 已完成功能
- 后端骨架与通义万相文生图接口
- 前端最小界面与前后端联调
- 后端提示词处理管线：Qwen 增强 + 风格预设（pixel-art / flat-vector / hand-drawn）
- GET /api/styles 接口
- 素材类型区分（character / icon / tile），独立配置文件 asset_types.py
- GET /api/asset-types 接口
- 前端新增素材类型与风格选择器（胶囊按钮，两维度自由组合）
- 去背景透明化（rembg 本地处理，remove_bg 开关，默认开启）
- 画廊式结果展示界面（卡片累积、棋盘格底纹、下载、删除）
- 精灵图打包与引擎导出（POST /api/pack，Shelf 装箱算法，JSON / Godot .tres 图集格式，ZIP 下载）
- README.md 起草（含技术栈、安装步骤、原创功能说明）

## 协作规范(重要)
- 一次只完成一个功能模块,不要一次性写多个功能
- API Key 一律从环境变量读取,禁止硬编码
- 改动保持模块化,新逻辑放独立文件
- 不要主动重构或改动与当前任务无关的代码

## 每日收尾(每个工作日最后一个任务时执行)
- 更新本文件「已完成功能」一节,补上当天新增的功能
- 在 docs/progress.md 中追加当天记录,只写客观事实:
  当天完成的功能、改动的主要文件、技术实现要点。
  按日期分节,不要覆盖之前的内容。
- 可编写适量的「遇到的问题」「设计取舍」等主观内容作为参考,
  这部分需要由开发者本人补充。
