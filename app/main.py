"""
main.py - FastAPI 后端入口
本地图片处理服务
"""
import os
import time
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.command_parser import parse_instruction
from app.image_utils import process_image, check_format_supported, OUTPUT_DIR, SUPPORTED_INPUT_FORMATS
from app.batch_utils import batch_process

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Image Processor Local", version="1.0.0")


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端页面"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)


@app.get("/health")
async def health():
    """健康检查 / Health check"""
    return {
        "success": True,
        "status": "ok",
        "message": "Local image processor is running / 本地图片处理服务正在运行",
    }


@app.get("/download/{filename}")
async def download(filename: str):
    """下载处理后的文件 / Download processed file"""
    file_path = (OUTPUT_DIR / filename).resolve()
    if not file_path.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied / 拒绝访问")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found / 文件不存在")
    return FileResponse(path=str(file_path), filename=filename)


@app.post("/api/process-command")
async def process_command(
    image: UploadFile = File(...),
    instruction: str = Form(...),
    compress_mode: Optional[str] = Form(None),
    quality: Optional[int] = Form(None),
):
    """处理单张图片"""
    # 检查文件格式
    if not image.filename:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "NO_FILENAME",
            "message": "No filename provided / 未提供文件名",
            "suggestion": "Please select an image file / 请选择图片文件",
        })

    if not check_format_supported(image.filename):
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "UNSUPPORTED_IMAGE_FORMAT",
            "message": "Unsupported image format / 不支持的图片格式",
            "suggestion": "Please upload JPG, PNG, WebP, BMP, or TIFF images / 请上传 JPG、PNG、WebP、BMP 或 TIFF 图片",
        })

    # 检查指令
    if not instruction or not instruction.strip():
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "EMPTY_INSTRUCTION",
            "message": "Instruction is empty / 指令为空",
            "suggestion": "Please enter a processing instruction / 请输入图片处理指令",
        })

    # 解析指令
    plan = parse_instruction(instruction)
    if not plan:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "INVALID_INSTRUCTION",
            "message": "Could not parse instruction / 无法解析指令",
            "suggestion": "Please check the instruction format / 请检查指令格式",
        })

    # API 参数覆盖 compress_mode
    if compress_mode in ("none", "lossy"):
        plan.setdefault("compress", {})["compress_mode"] = compress_mode

    # API 参数覆盖 quality（60-100，超出自动限制）
    if quality is not None:
        quality = max(60, min(100, quality))
        plan.setdefault("compress", {})["quality"] = quality

    # 保存上传文件到临时目录
    temp_path = str(UPLOAD_DIR / f"temp_{image.filename}")
    with open(temp_path, "wb") as f:
        content = await image.read()
        f.write(content)

    try:
        # 处理图片
        result = process_image(temp_path, image.filename, plan)
        result["tool"] = "process_command"
        return result
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/batch-process-command")
async def batch_process_command(
    images: List[UploadFile] = File(...),
    instruction: str = Form(...),
    zip_output: bool = Form(True),
    compress_mode: Optional[str] = Form(None),
    quality: Optional[int] = Form(None),
):
    """批量处理多张图片"""
    # 检查指令
    if not instruction or not instruction.strip():
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "EMPTY_INSTRUCTION",
            "message": "Instruction is empty / 指令为空",
            "suggestion": "Please enter a processing instruction / 请输入图片处理指令",
        })

    # 解析指令
    plan = parse_instruction(instruction)
    if not plan:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "INVALID_INSTRUCTION",
            "message": "Could not parse instruction / 无法解析指令",
            "suggestion": "Please check the instruction format / 请检查指令格式",
        })

    # API 参数覆盖 compress_mode
    if compress_mode in ("none", "lossy"):
        plan.setdefault("compress", {})["compress_mode"] = compress_mode

    # API 参数覆盖 quality（60-100，超出自动限制）
    if quality is not None:
        quality = max(60, min(100, quality))
        plan.setdefault("compress", {})["quality"] = quality

    # 保存所有上传文件
    temp_paths = []
    original_filenames = []

    for img in images:
        if not img.filename:
            continue

        temp_path = str(UPLOAD_DIR / f"temp_{img.filename}")
        with open(temp_path, "wb") as f:
            content = await img.read()
            f.write(content)

        temp_paths.append(temp_path)
        original_filenames.append(img.filename)

    if not temp_paths:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "NO_VALID_FILES",
            "message": "No valid image files provided / 未提供有效的图片文件",
            "suggestion": "Please select image files / 请选择图片文件",
        })

    try:
        # 批量处理
        result = batch_process(temp_paths, original_filenames, plan, zip_output)
        result["tool"] = "batch_process_command"
        return result
    finally:
        # 清理临时文件
        for temp_path in temp_paths:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class FolderProcessRequest(BaseModel):
    input_dir: str
    output_dir: str = ""
    instruction: str
    recursive: bool = False
    zip_output: bool = True
    compress_mode: Optional[str] = None
    quality: Optional[int] = None


@app.post("/api/batch-process-folder")
async def batch_process_folder(req: FolderProcessRequest):
    """文件夹批量处理 / Batch process a folder of images"""
    input_dir = Path(req.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "INPUT_FOLDER_NOT_FOUND",
            "message": f"Input folder not found: {req.input_dir} / 输入文件夹不存在",
            "suggestion": "Please check the input_dir path / 请检查输入文件夹路径",
        })

    # 解析指令
    plan = parse_instruction(req.instruction)
    if not plan:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "INSTRUCTION_NOT_RECOGNIZED",
            "message": "Could not parse instruction / 无法解析指令",
            "suggestion": "Please check the instruction format / 请检查指令格式",
        })

    # API 参数覆盖 compress_mode
    if req.compress_mode in ("none", "lossy"):
        plan.setdefault("compress", {})["compress_mode"] = req.compress_mode

    # API 参数覆盖 quality（60-100，超出自动限制）
    if req.quality is not None:
        quality = max(60, min(100, req.quality))
        plan.setdefault("compress", {})["quality"] = quality

    # 收集图片文件
    if req.recursive:
        all_files = list(input_dir.rglob("*"))
    else:
        all_files = list(input_dir.glob("*"))

    image_files = [f for f in all_files if f.is_file() and check_format_supported(f.name)]

    if not image_files:
        return JSONResponse(status_code=400, content={
            "success": False,
            "error_code": "NO_SUPPORTED_IMAGES_FOUND",
            "message": "No supported images found in folder / 文件夹中没有支持的图片",
            "suggestion": "Supported formats: JPG, PNG, WebP, BMP, TIFF",
        })

    # 确定输出目录
    if req.output_dir:
        output_dir = Path(req.output_dir)
    else:
        output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 处理每张图片
    results = []
    failed_results = []
    success_files = []
    success_filenames = []

    for img_path in image_files:
        original_filename = img_path.name
        result = process_image(str(img_path), original_filename, plan)

        if result.get("success"):
            output_filename = result["processed"]["filename"]
            src_path = OUTPUT_DIR / output_filename

            # 如果指定了不同输出目录，复制文件
            if output_dir.resolve() != OUTPUT_DIR.resolve():
                import shutil
                dst_path = output_dir / output_filename
                shutil.copy2(str(src_path), str(dst_path))
                success_files.append(str(dst_path))
            else:
                success_files.append(str(src_path))

            results.append({
                "success": True,
                "original_filename": original_filename,
                "output_filename": output_filename,
                "final_format": result["processed"]["format"],
                "final_width": result["processed"]["width"],
                "final_height": result["processed"]["height"],
                "final_file_size_kb": result["processed"]["file_size_kb"],
                "download_url": f"/download/{output_filename}",
                "preview_url": f"/download/{output_filename}",
            })
            success_filenames.append(output_filename)
        else:
            failed_results.append({
                "original_filename": original_filename,
                "error_code": result.get("error_code", "UNKNOWN_ERROR"),
                "message": result.get("message", "Unknown error"),
            })

    success_count = len(results)
    failed_count = len(failed_results)

    response: Dict[str, Any] = {
        "success": success_count > 0,
        "tool": "batch_process_folder",
        "message": "Batch folder processing completed / 文件夹批量处理完成" if success_count > 0 else "All images failed / 所有图片处理失败",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "total_files": len(image_files),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
        "failed_results": failed_results,
    }

    # 打包 ZIP
    if req.zip_output and success_count > 0:
        zip_filename = f"batch-processed-{int(time.time() * 1000)}.zip"
        zip_path = str(output_dir / zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path, arc_name in zip(success_files, success_filenames):
                if os.path.exists(file_path):
                    zf.write(file_path, arc_name)

        response["zip_filename"] = zip_filename
        response["zip_download_url"] = f"/download/{zip_filename}"

    return response


@app.get("/api/docs-info")
async def docs_info():
    """API 说明文档 / API documentation"""
    return {
        "service_name": "Local Image Processor",
        "version": "1.2.0",
        "description": "Local image format conversion, resize, crop and compression tool / 本地图片格式转换、缩放、裁剪和压缩工具",
        "supported_input_formats": sorted(list(SUPPORTED_INPUT_FORMATS)),
        "supported_output_formats": ["webp", "jpg", "png"],
        "compress_modes": {
            "none": "Original quality, format conversion only, quality=100 / 原图转换，不压缩，quality=100",
            "lossy": "Enable compression with configurable quality (60-100, default 90) / 开启压缩，可设置质量（60-100，默认90）",
        },
        "endpoints": {
            "GET /health": "Health check / 健康检查",
            "POST /api/process-command": "Process single image / 单张图片处理 (multipart/form-data: image, instruction, compress_mode, quality)",
            "POST /api/batch-process-command": "Batch process uploaded images / 批量上传处理 (multipart/form-data: images[], instruction, zip_output, compress_mode, quality)",
            "POST /api/batch-process-folder": "Batch process folder / 文件夹批量处理 (JSON: input_dir, output_dir, instruction, recursive, zip_output, compress_mode, quality)",
            "GET /download/{filename}": "Download processed file / 下载处理后的文件",
            "GET /api/docs-info": "This documentation / 本文档",
        },
        "example_instructions": [
            "convert to WebP, no compress（仅格式转换，不压缩）",
            "宽度1000px，转成WebP，压缩到300KB以内",
            "裁剪成800x800，转成JPG",
            "压缩到200KB以内",
            "resize width to 1200px, convert to WebP",
            "独立站产品主图",
        ],
        "example_curl": {
            "health": 'curl http://127.0.0.1:8000/health',
            "single_no_compress": 'curl -X POST "http://127.0.0.1:8000/api/process-command" -F "image=@sample.png" -F "instruction=convert to WebP" -F "compress_mode=none"',
            "single_compress": 'curl -X POST "http://127.0.0.1:8000/api/process-command" -F "image=@sample.png" -F "instruction=convert to WebP" -F "compress_mode=lossy" -F "quality=90"',
            "batch": 'curl -X POST "http://127.0.0.1:8000/api/batch-process-command" -F "images=@a.png" -F "images=@b.jpg" -F "instruction=转成WebP" -F "zip_output=true"',
            "folder": 'curl -X POST "http://127.0.0.1:8000/api/batch-process-folder" -H "Content-Type: application/json" -d \'{"input_dir":"D:/input","instruction":"convert to WebP","compress_mode":"none"}\'',
        },
    }


# 挂载静态文件（在路由之后）
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
