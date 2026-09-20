# Harvest format

`collect_enterprise_sources.py` 从 `knowledge_base/seeds/official_sources.json` 读取入口，保存小型 HTML/README 快照的元数据和 SHA-256。原始页面不应自动被当作事实卡；收集器输出的 `extraction_status` 和 `content_hash` 只证明抓取行为。

建议保存：

- `raw/<source_id>.json`：URL、HTTP 状态、响应头、页面标题、文本摘要、哈希和抓取日期；
- `raw/<source_id>.body`：在许可允许、体积可控时保存原文；大文件只保存 URL、版本和哈希；
- `manifest.jsonl`：每次抓取的工具版本、seed 文件哈希、失败原因和重试记录。

不要抓取或提交私有数据、登录态、患者级数据、商业模型权重或受限附件。对 GitHub 仓库优先记录 commit/tag 和 API 元数据；对大型数据集只记录官方 accession、大小、许可证和下载验证日志。
