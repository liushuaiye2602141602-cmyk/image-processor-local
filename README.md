# Image Processor Local / 本地图片处理工具

一个纯本地运行的图片格式转换、缩放、裁剪和压缩工具。

不需要 Docker，不需要外部 API，不需要数据库，不需要登录。开放稳定 API，支持 n8n 调用。

## 功能

- 图片格式转换（WebP / JPG / PNG）
- 按宽度或高度等比例缩放
- 改成指定尺寸（白底补边）
- 居中裁剪成指定尺寸
- 压缩到指定大小（如 300KB 以内）
- 单张处理和批量处理
- 批量处理自动打包 ZIP 下载
- 文件夹批量处理（API 接口）
- 支持一句话自然语言指令（中文 / 英文）
- 开放 REST API，支持 n8n 自动化调用

## 环境要求

- Windows 10 / 11
- Python 3.8 或更高版本

## 快速启动

### 第一次使用

1. 双击 `install_requirements.bat` — 自动创建虚拟环境并安装依赖
2. 双击 `start_image_processor.bat` — 启动服务并自动打开浏览器

### 之后每次使用

双击 `start_image_processor.bat` 即可。

### 停止服务

双击 `stop_image_processor.bat`，或直接关闭启动窗口。

### 创建桌面快捷方式

双击 `create_desktop_shortcut.bat`，桌面会出现「Local Image Processor」快捷方式。

## 网页端使用

1. 拖拽或点击上传图片（支持多张）
2. 输入处理指令
3. 点击「开始处理」
4. 查看结果，下载处理后的图片

### 快捷按钮

| 按钮 | 指令 | 效果 |
|------|------|------|
| 产品主图 | 独立站产品主图 | 1000x1000 白底补边 WebP 质量88 |
| WebP 300KB | width 1000px, convert to WebP, compress under 300KB | 宽度1000 WebP 300KB以内 |
| JPG 200KB | width 800px, convert to JPG, compress under 200KB | 宽度800 JPG 200KB以内 |
| 只压缩 | compress under 300KB | 不改尺寸 只压缩 |
| 裁剪 1000x1000 | crop to 1000x1000, convert to WebP | 居中裁剪 WebP |

## API 接口

服务地址：`http://127.0.0.1:8000`

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/process-command` | POST | 单张图片处理 (form-data) |
| `/api/batch-process-command` | POST | 批量上传处理 (form-data) |
| `/api/batch-process-folder` | POST | 文件夹批量处理 (JSON) |
| `/download/{filename}` | GET | 下载处理结果 |
| `/api/docs-info` | GET | API 文档说明 |

### 单图 API 示例

```bash
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\path\to\image.png" ^
  -F "instruction=width 1000px, convert to WebP, compress under 300KB"
```

### 文件夹批量 API 示例

```bash
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\path\\to\\folder\",\"instruction\":\"convert to WebP\"}"
```

详细 API 文档请查看 [API_FOR_N8N.md](API_FOR_N8N.md)。

## 支持的指令示例

### 缩放

| 指令 | 效果 |
|------|------|
| width 1000px / 宽度1000px | 宽度1000，高度等比例 |
| height 800px / 高度800px | 高度800，宽度等比例 |
| 1000x1000 / 改成1000x1000 | 1000x1000 白底补边 |
| stretch to 1000x1000 / 拉伸改成1000x1000 | 1000x1000 强制拉伸 |
| crop to 1000x1000 / 裁剪成1000x1000 | 居中裁剪 1000x1000 |
| no resize / 不改尺寸 | 保持原尺寸 |

### 格式转换

| 指令 | 效果 |
|------|------|
| convert to webp / 转成WebP | 输出 WebP 格式 |
| convert to jpg / 转成JPG | 输出 JPG 格式（透明底变白底） |
| convert to png / 转成PNG | 输出 PNG 格式 |

### 压缩

| 指令 | 效果 |
|------|------|
| compress / 压缩 | 使用格式默认质量（WebP=88, JPG=90） |
| compress under 300KB / 压缩到300KB以内 | 尝试压缩到 300KB |
| less than 1MB / 小于1MB | 尝试压缩到 1MB |
| quality 80 / 质量80 | 指定输出质量 80 |

### 组合指令

```
width 1000px, convert to WebP, compress under 300KB
crop to 1000x1000, save as jpg, quality 85
height 800px, save as png
```

### 常用预设

| 指令 | 尺寸 | 格式 | 质量 |
|------|------|------|------|
| website product image / 独立站产品主图 | 1000x1000 白底补边 | WebP | 88 |
| blog image / 博客配图 | 1200x800 | WebP | 88 |
| banner image / 网站Banner | 1200x600 | WebP | 88 |
| LinkedIn square / LinkedIn方图 | 1080x1080 | WebP | 88 |
| Instagram portrait / Instagram竖图 | 1080x1350 | WebP | 88 |

## 压缩质量策略

| 格式 | 默认质量 | 最低质量 |
|------|---------|---------|
| WebP | 88 | 72 |
| JPG | 90 | 75 |

- 压缩到目标大小时，每次降低质量 3
- 降到最低质量后仍大于目标大小时，不再继续牺牲画质
- 返回 `COMPRESSION_TARGET_NOT_RECAHED` 警告
- 保留最终输出文件

## 支持的图片格式

### 输入

JPG, JPEG, PNG, WebP, BMP, TIF, TIFF

### 输出

WebP, JPG, PNG

## n8n 调用

本项目开放 REST API，可直接用 n8n 的 HTTP Request 节点调用。

推荐使用 `/api/batch-process-folder` 接口：只需传入文件夹路径和处理指令。

详细配置请查看 [API_FOR_N8N.md](API_FOR_N8N.md)。

## 常见问题

### Q: 双击 bat 没反应？

A: 确认已安装 Python 3.8+，且在系统 PATH 中。打开 cmd 输入 `python --version` 检查。

### Q: pip install 报错？

A: 尝试升级 pip：`python -m pip install --upgrade pip`

### Q: 端口 8000 被占用？

A: 先运行 `stop_image_processor.bat`，或修改启动脚本中的端口号。

### Q: 压缩到指定大小达不到？

A: 系统会用最低质量保存（WebP 72, JPG 75），并返回 warning 提示，不会继续牺牲画质。

### Q: 中文指令在 curl 中乱码？

A: Windows curl 有编码限制。建议用 Python requests 或 n8n HTTP Request 节点调用，中文指令在网页端和 API 中都能正常解析。

## 项目结构

```
image_processor_local/
  app/
    __init__.py
    main.py                   # FastAPI 后端入口 + API 端点
    command_parser.py         # 一句话指令解析
    image_utils.py            # 图片处理核心（含压缩质量策略）
    batch_utils.py            # 批量处理 + ZIP 打包
  static/
    index.html                # 前端页面
    style.css                 # 样式
    app.js                    # 前端逻辑
  outputs/                    # 处理结果输出目录
  uploads/                    # 上传临时目录
  requirements.txt            # Python 依赖
  start_image_processor.bat   # 一键启动
  install_requirements.bat    # 安装依赖
  stop_image_processor.bat    # 停止服务
  create_desktop_shortcut.bat # 创建桌面快捷方式
  API_FOR_N8N.md              # API 接口文档（n8n 调用指南）
  QUICK_START.md              # 快速启动指南
  README.md                   # 本文档
```
