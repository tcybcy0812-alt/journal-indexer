# 📖 期刊论文索引器

输入期刊目录链接，一键爬取所有论文的标题、作者、摘要、原文链接等信息。支持手机 Expo Go 扫码使用。

## 🏗 架构

```
手机 Expo App  ←── API ──→  电脑 Python 后端
(Expo Go 扫码)              (FastAPI + SQLite)
```

## 📁 项目结构

```
journal-indexer/
├── backend/            # Python 后端
│   ├── main.py        # FastAPI API 服务
│   ├── database.py    # SQLite 数据库
│   ├── models.py      # 数据模型
│   ├── crawler/       # 爬虫模块
│   │   ├── arxiv.py   # arXiv 适配
│   │   ├── science.py # Science 系列
│   │   ├── nature.py  # Nature 系列
│   │   └── generic.py # 通用爬虫
│   └── requirements.txt
├── mobile/             # Expo 前端
│   ├── app/
│   │   ├── (tabs)/    # Tab 页面（爬取 + 历史）
│   │   └── paper/     # 论文详情页
│   └── components/    # UI 组件
└── README.md
```

## 🚀 使用方法

### 1. 启动后端

```bash
cd backend
pip3 install -r requirements.txt
python main.py
```

后端会在 **http://0.0.0.0:8000** 启动。

### 2. 确认 IP 地址

```bash
ipconfig getifaddr en0
```

确保 `mobile/config.ts` 中的 `API_BASE` 与你的 IP 一致。

### 3. 启动前端

```bash
cd mobile
npm install
npx expo start
```

终端会显示一个二维码。

### 4. 手机扫码

1. 下载 **Expo Go**（iOS App Store / Android Play Store）
2. 确保手机和电脑在同一 WiFi
3. 用 Expo Go 扫码
4. 输入期刊链接，开始爬取！

## 🔗 支持的期刊

- ✅ arXiv (arxiv.org)
- ✅ Nature 系列 (nature.com)
- ✅ Science 系列 (science.org)
- ✅ 其他通用期刊网站（自动尝试多种解析策略）

## 📡 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/crawl | 爬取期刊 URL |
| GET | /api/papers | 获取论文列表 |
| GET | /api/papers/search?q= | 搜索论文 |
| GET | /api/papers/{id} | 论文详情 |
| GET | /api/journals | 期刊列表 |
| GET | /api/papers/export | 导出 Excel |
