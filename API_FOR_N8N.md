# API 接口文档（n8n 调用指南）

服务地址：`http://127.0.0.1:8000`

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
  - `compress_mode`（可选）：`none` = 不压缩仅转换格式 / `lossy` = 开启压缩
  - `quality`（可选）：压缩质量 72-100，仅 compress_mode=lossy 时生效

### curl 示例

```bash
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=width 1000px, convert to WebP, compress under 300KB"
```

### 不压缩模式（仅转换格式）

```bash
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "compress_mode=none"
```

### 压缩模式（指定质量）

```bash
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\n8n-files\sample.png" ^
  -F "instruction=convert to WebP" ^
  -F "compress_mode=lossy" ^
  -F "quality=85"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/process-command` |
| Body Content Type | Form Data |
| Form Data Fields | `image` = 二进制文件 / `instruction` = 文本 / `compress_mode` = none 或 lossy（可选） / `quality` = 72-100（可选） |

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
    "width": 1000,
    "height": 750,
    "file_size_kb": 45.2,
    "download_url": "/download/sample-1779271590493-abcd.webp",
    "preview_url": "/download/sample-1779271590493-abcd.webp",
    "quality_used": 88,
    "target_kb": 300,
    "final_file_size_kb": 45.2,
    "size_target_reached": true,
    "warnings": []
  },
  "operation_plan": {
    "resize": { "mode": "width", "width": 1000 },
    "crop": {},
    "convert": { "format": "webp" },
    "compress": { "target_kb": 300 }
  },
  "warnings": []
}
```

### 常用指令示例

```
width 1000px, convert to WebP, compress under 300KB
resize width to 800px, convert to JPG
compress under 200KB
crop to 1000x1000, convert to WebP
convert to WebP, no compress（仅格式转换，不压缩）
website product image
```

---

## 3. 批量上传处理

**POST** `/api/batch-process-command`

- 请求类型：`multipart/form-data`
- 字段：
  - `images`：多个图片文件（同名字段）
  - `instruction`：处理指令
  - `zip_output`：`true` 或 `false`（默认 `true`）
  - `compress_mode`（可选）：`none` 或 `lossy`
  - `quality`（可选）：72-100

### curl 示例

```bash
curl -X POST "http://127.0.0.1:8000/api/batch-process-command" ^
  -F "images=@D:\n8n-files\sample1.png" ^
  -F "images=@D:\n8n-files\sample2.jpg" ^
  -F "instruction=width 1000px, convert to WebP" ^
  -F "zip_output=true"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/batch-process-command` |
| Body Content Type | Form Data |
| Form Data Fields | `images` = 多个二进制文件 / `instruction` = 文本 / `zip_output` = true |

### 返回示例

```json
{
  "success": true,
  "tool": "batch_process_command",
  "message": "Batch image processing completed / 批量图片处理完成",
  "total_files": 2,
  "success_count": 2,
  "failed_count": 0,
  "results": [
    {
      "success": true,
      "original_filename": "sample1.png",
      "output_filename": "sample1-1779271590493-abcd.webp",
      "final_format": "WEBP",
      "final_width": 1000,
      "final_height": 750,
      "final_file_size_kb": 45.2,
      "download_url": "/download/sample1-1779271590493-abcd.webp",
      "preview_url": "/download/sample1-1779271590493-abcd.webp"
    }
  ],
  "failed_results": [],
  "zip_filename": "batch-processed-1779271590500.zip",
  "zip_download_url": "/download/batch-processed-1779271590500.zip"
}
```

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
  "instruction": "width 1000px, convert to WebP, compress under 300KB",
  "recursive": false,
  "zip_output": true,
  "compress_mode": "none"
}
```

- `compress_mode`（可选）：`none` = 不压缩仅转换格式 / `lossy` = 开启压缩

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| input_dir | string | 是 | 输入文件夹路径 |
| output_dir | string | 否 | 输出文件夹（默认 outputs/） |
| instruction | string | 是 | 处理指令 |
| recursive | bool | 否 | 是否递归子文件夹（默认 false） |
| zip_output | bool | 否 | 是否生成 ZIP（默认 true） |
| compress_mode | string | 否 | `none`（不压缩）或 `lossy`（压缩） |
| quality | int | 否 | 压缩质量 72-100，仅 lossy 时生效 |

### curl 示例

```bash
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\n8n-files\\input\",\"instruction\":\"width 1000px, convert to WebP\",\"recursive\":false,\"zip_output\":true}"
```

### n8n HTTP Request 节点配置

| 配置项 | 值 |
|--------|-----|
| Method | POST |
| URL | `http://127.0.0.1:8000/api/batch-process-folder` |
| Body Content Type | JSON |
| JSON Body | 见上方请求体示例 |

### 返回示例

```json
{
  "success": true,
  "tool": "batch_process_folder",
  "message": "Batch folder processing completed / 文件夹批量处理完成",
  "input_dir": "D:\\n8n-files\\input",
  "output_dir": "D:\\n8n-files\\output",
  "total_files": 10,
  "success_count": 10,
  "failed_count": 0,
  "results": [...],
  "failed_results": [],
  "zip_filename": "batch-processed-1779271590500.zip",
  "zip_download_url": "/download/batch-processed-1779271590500.zip"
}
```

---

## 5. 下载文件

**GET** `/download/{filename}`

下载 outputs 文件夹中的处理结果或 ZIP 文件。

```
http://127.0.0.1:8000/download/sample-1779271590493-abcd.webp
```

- 返回文件流，可直接在浏览器打开或下载
- 文件不存在返回 404

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
2. **HTTP Request**：调用 `/api/batch-process-folder`
3. **IF**：检查 `success` 字段
4. **后续节点**：发送通知、移动文件等

### 场景 2：Webhook 接收图片处理

1. **Webhook**：接收图片 URL 或文件
2. **HTTP Request**：下载图片到本地
3. **HTTP Request**：调用 `/api/process-command`
4. **Response**：返回处理结果

### 场景 3：批量压缩产品图

1. **HTTP Request**：调用 `/api/batch-process-folder`
   - input_dir: 产品图源文件夹
   - instruction: `website product image`
2. **HTTP Request**：调用下载链接获取 ZIP
3. **后续节点**：上传到 CDN 或发送邮件
