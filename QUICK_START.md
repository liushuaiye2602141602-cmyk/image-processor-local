# 快速启动指南

## 第一步：安装依赖

双击 `install_requirements.bat`

等待安装完成（首次约 1-2 分钟）。

## 第二步：启动服务

双击 `start_image_processor.bat`

浏览器会自动打开 http://127.0.0.1:8000

## 第三步：开始使用

### 网页端使用

1. 拖拽或点击上传图片
2. 输入处理指令，例如：
   - `width 1000px, convert to WebP, compress under 300KB`
   - `裁剪成 800x800，转成 JPG`
   - `compress under 200KB`
3. 选择处理模式：
   - **原图转换**（默认）：不压缩，只转换格式，适合产品图
   - **推荐压缩**：quality=90，适合网站图片优化
   - **自定义压缩**：手动设置 quality（60-100）
4. 点击「开始处理」
5. 下载处理后的图片

### API 调用

```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 原图转换（不压缩，quality=100）
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\path\to\image.png" ^
  -F "instruction=convert to WebP" ^
  -F "mode=original"

# 推荐压缩（quality=90）
curl -X POST "http://127.0.0.1:8000/api/process-command" ^
  -F "image=@D:\path\to\image.png" ^
  -F "instruction=convert to WebP" ^
  -F "mode=recommended"

# 文件夹批量处理
curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" ^
  -H "Content-Type: application/json" ^
  -d "{\"input_dir\":\"D:\\path\\to\\folder\",\"instruction\":\"convert to WebP\",\"mode\":\"original\"}"
```

## 停止服务

双击 `stop_image_processor.bat`

或直接关闭启动窗口。

## 常见问题

**Q: 双击 bat 没反应？**
A: 确认已安装 Python 3.8+，且在系统 PATH 中。打开 cmd 输入 `python --version` 检查。

**Q: 提示端口被占用？**
A: 先运行 `stop_image_processor.bat`，或重启电脑。

**Q: 中文指令在 curl 中乱码？**
A: Windows curl 有编码限制，建议用 Python requests 或 n8n HTTP Request 节点调用，中文指令在网页端和 API 中都能正常解析。

**Q: 图片处理后画质损失大？**
A: 当前默认策略已优化：WebP 默认质量 90，JPG 默认质量 90。如仍不满意，可手动指定更高质量，如 `quality 95`。
