"""
batch_utils.py - 批量图片处理模块
"""
import os
import time
import zipfile
from pathlib import Path
from typing import Dict, Any, List

from app.image_utils import process_image, check_format_supported, OUTPUT_DIR


def batch_process(
    file_paths: List[str],
    original_filenames: List[str],
    plan: Dict[str, Any],
    zip_output: bool = True,
) -> Dict[str, Any]:
    """
    批量处理多张图片

    Args:
        file_paths: 上传文件的临时路径列表
        original_filenames: 原始文件名列表
        plan: 操作计划
        zip_output: 是否打包成 ZIP

    Returns:
        批量处理结果
    """
    results: List[Dict[str, Any]] = []
    failed_results: List[Dict[str, Any]] = []
    success_files: List[str] = []
    success_filenames: List[str] = []

    for file_path, original_filename in zip(file_paths, original_filenames):
        # 检查格式
        if not check_format_supported(original_filename):
            failed_results.append({
                "original_filename": original_filename,
                "error_code": "UNSUPPORTED_IMAGE_FORMAT",
                "message": "Unsupported image format / 不支持的图片格式",
            })
            continue

        # 处理单张图片
        result = process_image(file_path, original_filename, plan)

        if result.get("success"):
            output_filename = result["processed"]["filename"]
            results.append({
                "success": True,
                "original_filename": original_filename,
                "output_filename": output_filename,
                "final_format": result["processed"]["format"],
                "final_width": result["processed"]["width"],
                "final_height": result["processed"]["height"],
                "final_file_size_kb": result["processed"]["file_size_kb"],
                "download_url": result["processed"]["download_url"],
                "preview_url": result["processed"]["preview_url"],
            })
            success_files.append(str(OUTPUT_DIR / output_filename))
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
        "message": "Batch image processing completed / 批量图片处理完成" if success_count > 0 else "All images failed / 所有图片处理失败",
        "total_files": len(file_paths),
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
        "failed_results": failed_results,
    }

    # 打包 ZIP
    if zip_output and success_count > 0:
        zip_filename = f"batch-processed-{int(time.time() * 1000)}.zip"
        zip_path = str(OUTPUT_DIR / zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path, arc_name in zip(success_files, success_filenames):
                if os.path.exists(file_path):
                    zf.write(file_path, arc_name)

        response["zip_filename"] = zip_filename
        response["zip_download_url"] = f"/download/{zip_filename}"

    return response
