# API 接口文档（n8n 调用指南）

服务地址：`http://127.0.0.1:8000`

---

## 处理模式

所有 API 接口支持 `mode` 参数，用于指定图片处理模式：

| mode | 说明 | quality | 适用场景 |
|------|------|---------|----------|
| `original` | 原图转换：不压缩，不改尺寸，只转换格式 | 100（固定） | 产品图、Banner、详情页、独立站高清图 |
| `recommended` | 推荐压缩：清晰度优先，适当减小体积 | 90（默认） | 独立站网站图片优化 |
| `custom` | 自定义压缩：用户手动设置 quality | 60-100（用户指定） | 灵活控制体积和清晰度 |

> **quality 说明**：quality 不是"文件压缩百分比"，而是图片编码质量参数。quality 越高越清晰，文件可能越大。低于 70 可能导致明显模糊，不推荐用于产品图或独立站主图。

---

## 1. 健康检查

**GET** `/health`

检查服务是否在线。

```bash
curl http://127.0.0.1:8000/health
```

返回：

```json
{
  "success": true,
  "status": "ok",
  "message": "Local image processor is running / 本地图片处理服务正在运行"
}
```

---

## 2. 单张图片处理

**POST** `/api/process-command`

- 请求类型：`multipart/form-data`
- 字段：
  - `image`：图片文件
  - `instruction`：处理指令（自然语言）
  - `mode`（推荐）：`original` / `recommended` / `custom`
  - `compress_mode`（可选，兼容旧版）：`none` = 原图转换 / `lossy` = 开启压缩
  - `quality`（可选）：压缩质量 60-100，默认 90，仅 compress 时生效

### curl 示例

```bash
# 原图转换（不压缩，quality=100，不改尺寸）
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "mode=original"

# 推荐压缩（quality=90）
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "mode=recommended"

# 自定义压缩质量（quality=80）
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "mode=custom" ^
  -F "quality=80"
```

### 兼容旧版 compress_mode 参数

```bash
# 等同于 mode=original
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "compress_mode=none"

# 等同于 mode=recommended
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "compress_mode=lossy" ^
  -F "quality=90"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/process-command` |
| Body Content Type | Form Data |
| Form Data Fields | `image` = 二进制文件 / `instruction` = 文本 / `mode` = original 或 recommended 或 custom / `quality` = 60-100（可选，默认 90） |

### 返回示例

```json
{
  "success": true,
  "tool": "process_command",
  "message": "Image processed successfully / 图片处理成功",
  "original": {
    "filename": "sample.png",
    "format": "PNG",
    "width": 2000,
    "height": 1500,
    "file_size_kb": 512.5
  },
  "processed": {
    "filename": "sample-1779271590493-abcd.webp",
    "format": "WEBP",
    "width": 2000,
    "height": 1500,
    "file_size_kb": 480.3,
    "download_url": "/download/sample-1779271590493-abcd.webp",
    "preview_url": "/download/sample-1779271590493-abcd.webp",
    "quality_used": 100,
    "compress_mode": "none",
    "target_kb": null,
    "final_file_size_kb": 480.3,
    "size_target_reached": true,
    "warnings": []
  },
  "operation_plan": {
    "resize": {},
    "crop": {},
    "convert": { "format": "webp" },
    "compress": { "compress_mode": "none" }
  }
}
```

### 常用指令示例

```
convert to WebP                    # 转成 WebP
width 1000px, convert to WebP      # 宽度 1000，转 WebP
compress under 300KB               # 压缩到 300KB 以内
crop to 1000x1000, convert to WebP # 裁剪 1000x1000，转 WebP
website product image              # 独立站产品主图预设
```

---

## 3. 批量上传处理

**POST** `/api/batch-process-command`

- 请求类型：`multipart/form-data`
- 字段：
  - `images`：多个图片文件（同名字段）
  - `instruction`：处理指令
  - `zip_output`：`true` 或 `false`（默认 `true`）
  - `mode`（推荐）：`original` / `recommended` / `custom`
  - `compress_mode`（可选，兼容旧版）：`none` 或 `lossy`
  - `quality`（可选）：60-100，默认 90

### curl 示例

```bash
# 推荐压缩批量处理
curl -X POST "http://127.0.0.1:8000/api/batch-process-command" ^
  -F "images=@D:\n8n-files\sample1.png" ^
  -F "images=@D:\n8n-files\sample2.jpg" ^
  -F "instruction=width 1000px, convert to WebP" ^
  -F "mode=recommended" ^
  -F "zip_output=true"

# 原图转换批量处理
curl -X POST "http://127.0.0.1:8000/api/batch-process-command" ^
  -F "images=@D:\n8n-files\sample1.png" ^
  -F "images=@D:\n8n-files\sample2.jpg" ^
  -F "instruction=convert to WebP" ^
  -F "mode=original" ^
  -F "zip_output=true"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/batch-process-command` |
| Body Content Type | Form Data |
| Form Data Fields | `images` = 多个二进制文件 / `instruction` = 文本 / `mode` = original 或 recommended / `zip_output` = true |

---

## 4. 文件夹批量处理

**POST** `/api/batch-process-folder`

- 请求类型：`application/json`
- 用途：n8n 本地自动化，直接传文件夹路径

### 请求体

```json
{
  "input_dir": "D:\\n8n-files\\input",
  "output_dir": "D:\\n8n-files\\output",
  "instruction": "convert to WebP",
  "mode": "original",
  "recursive": false,
  "zip_output": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| input_dir | string | 是 | 输入文件夹路径 |
| output_dir | string | 否 | 输出文件夹（默认 outputs/） |
| instruction | string | 是 | 处理指令 |
| mode | string | 否 | `original`（原图转换）/ `recommended`（推荐压缩）/ `custom`（自定义） |
| compress_mode | string | 否 | 兼容旧版：`none` 或 `lossy` |
| quality | int | 否 | 压缩质量 60-100（默认 90），仅 compress 时生效 |
| recursive | bool | 否 | 是否递归子文件夹（默认 false） |
| zip_output | bool | 否 | 是否生成 ZIP（默认 true） |

### curl 示例

```bash
# 原图转换
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\n8n-files\\input\",\"instruction\":\"convert to WebP\",\"mode\":\"original\"}"

# 推荐压缩
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\n8n-files\\input\",\"instruction\":\"convert to WebP\",\"mode\":\"recommended\"}"

# 自定义压缩质量
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\n8n-files\\input\",\"instruction\":\"convert to WebP\",\"mode\":\"custom\",\"quality\":80}"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/batch-process-folder` |
| Body Content Type | JSON |
| JSON Body | 见上方请求体示例 |

---

## 5. 下载文件

**GET** `/download/{filename}`

下载 outputs 文件夹中的处理结果或 ZIP 文件。

```
http://127.0.0.1:8000/download/sample-1779271590493-abcd.webp
```

---

## 6. API 说明

**GET** `/api/docs-info`

返回所有端点说明、支持的格式、示例指令和示例 curl 命令。

---

## 错误处理

所有接口失败时统一返回格式：

```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "English message / 中文提示",
  "suggestion": "English suggestion / 中文建议"
}
```

### 错误码列表

| error_code | 说明 |
|-----------|------|
| NO_IMAGE_UPLOADED | 没有上传图片 |
| NO_FILENAME | 文件名为空 |
| EMPTY_INSTRUCTION | 没有输入指令 |
| UNSUPPORTED_IMAGE_FORMAT | 不支持的图片格式 |
| INPUT_FOLDER_NOT_FOUND | 文件夹不存在 |
| NO_SUPPORTED_IMAGES_FOUND | 文件夹里没有支持的图片 |
| INSTRUCTION_NOT_RECOGNIZED | 指令无法识别 |
| PROCESSING_ERROR | 图片处理失败 |
| NO_VALID_FILES | 没有有效的图片文件 |

---

## n8n 工作流建议

### 场景 1：监控文件夹自动处理

1. **Trigger**：Schedule Trigger（定时）或 On File Change（文件变化）
2. **HTTP Request**：调用 `/api/batch-process-folder`，`mode=original`
3. **IF**：检查 `success` 字段
4. **后续节点**：发送通知、移动文件等

### 场景 2：Webhook 接收图片处理

1. **Webhook**：接收图片 URL 或文件
2. **HTTP Request**：下载图片到本地
3. **HTTP Request**：调用 `/api/process-command`，`mode=recommended`
4. **Response**：返回处理结果

### 场景 3：批量压缩产品图

1. **HTTP Request**：调用 `/api/batch-process-folder`
   - input_dir: 产品图源文件夹
   - instruction: `website product image`
   - mode: `recommended`
2. **HTTP Request**：调用下载链接获取 ZIP
3. **后续节点**：上传到 CDN 或发送邮件
