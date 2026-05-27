"""
image_utils.py - 图片处理核心模块
使用 Pillow 实现图片的缩放、裁剪、格式转换和压缩
"""
import os
import time
import random
import string
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from PIL import Image, ExifTags

# 支持的输入格式
SUPPORTED_INPUT_FORMATS = {"jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif"}
# 支持的输出格式
SUPPORTED_OUTPUT_FORMATS = {"webp", "jpg", "jpeg", "png"}
# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"

# 压缩质量常量
WEBP_DEFAULT_QUALITY = 90
JPEG_DEFAULT_QUALITY = 90
MIN_QUALITY = 60
JPEG_MIN_QUALITY = 60
QUALITY_STEP = 3


def _get_default_quality(target_format: str) -> int:
    """根据输出格式返回推荐的默认质量"""
    fmt = target_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt == "webp":
        return WEBP_DEFAULT_QUALITY
    if fmt == "jpg":
        return JPEG_DEFAULT_QUALITY
    return WEBP_DEFAULT_QUALITY


def _get_min_quality(target_format: str) -> int:
    """根据输出格式返回最低质量"""
    fmt = target_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"
    if fmt == "jpg":
        return JPEG_MIN_QUALITY
    return MIN_QUALITY


# 格式映射：内部格式名 → Pillow save format
_SAVE_FORMAT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "webp": "WEBP",
    "bmp": "BMP",
    "tif": "TIFF",
    "tiff": "TIFF",
}


def _to_save_format(target_format: str) -> str:
    """将任意格式名标准化为 Pillow save format（如 'jpg' → 'JPEG'）"""
    return _SAVE_FORMAT_MAP.get(target_format.lower(), target_format.upper())


def get_image_info(img: Image.Image, file_size_bytes: int) -> Dict[str, Any]:
    """获取图片基本信息"""
    return {
        "format": img.format or "UNKNOWN",
        "width": img.width,
        "height": img.height,
        "file_size_kb": round(file_size_bytes / 1024, 2),
    }


def fix_exif_orientation(img: Image.Image) -> Image.Image:
    """修正 EXIF 方向信息"""
    try:
        exif = img.getexif()
        if exif is None:
            return img

        orientation_key = None
        for key, value in ExifTags.TAGS.items():
            if value == "Orientation":
                orientation_key = key
                break

        if orientation_key is None or orientation_key not in exif:
            return img

        orientation = exif[orientation_key]
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return img


def generate_output_filename(original_name: str, target_format: str) -> str:
    """生成输出文件名，避免覆盖"""
    name_parts = os.path.splitext(original_name)
    base_name = name_parts[0]
    timestamp = int(time.time() * 1000)
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    ext = target_format.lower()
    if ext == "jpeg":
        ext = "jpg"
    return f"{base_name}-{timestamp}-{random_suffix}.{ext}"


def resize_image(img: Image.Image, resize_params: Dict[str, Any]) -> Image.Image:
    """根据参数调整图片尺寸"""
    if not resize_params:
        return img

    mode = resize_params.get("mode", "none")

    if mode == "none":
        return img

    if mode == "width":
        target_width = resize_params["width"]
        ratio = target_width / img.width
        target_height = int(img.height * ratio)
        return img.resize((target_width, target_height), Image.LANCZOS)

    if mode == "height":
        target_height = resize_params["height"]
        ratio = target_height / img.height
        target_width = int(img.width * ratio)
        return img.resize((target_width, target_height), Image.LANCZOS)

    if mode == "exact":
        target_width = resize_params["width"]
        target_height = resize_params["height"]
        stretch = resize_params.get("stretch", False)

        if stretch:
            return img.resize((target_width, target_height), Image.LANCZOS)

        # 等比例缩放后白底补边
        ratio = min(target_width / img.width, target_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)
        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # 创建白底画布
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            canvas = Image.new("RGBA", (target_width, target_height), (255, 255, 255, 255))
            if resized.mode != "RGBA":
                resized = resized.convert("RGBA")
        else:
            canvas = Image.new("RGB", (target_width, target_height), (255, 255, 255))
            if resized.mode != "RGB":
                resized = resized.convert("RGB")

        # 居中粘贴
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        canvas.paste(resized, (paste_x, paste_y))
        return canvas

    return img


def crop_image(img: Image.Image, crop_params: Dict[str, Any]) -> Image.Image:
    """居中裁剪图片"""
    if not crop_params:
        return img

    target_width = crop_params["width"]
    target_height = crop_params["height"]

    # 计算裁剪区域（居中）
    ratio = max(target_width / img.width, target_height / img.height)
    new_width = int(img.width * ratio)
    new_height = int(img.height * ratio)

    # 先缩放
    resized = img.resize((new_width, new_height), Image.LANCZOS)

    # 居中裁剪
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    return resized.crop((left, top, right, bottom))


def convert_format(img: Image.Image, target_format: str) -> Image.Image:
    """转换图片格式（处理颜色模式）"""
    target_format = target_format.lower()
    if target_format == "jpeg":
        target_format = "jpg"

    if target_format == "jpg":
        # JPG 不支持透明度，转为 RGB 白底
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
    elif target_format == "webp":
        # WebP 支持透明度
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode == "LA":
            img = img.convert("RGBA")
    elif target_format == "png":
        if img.mode == "P":
            img = img.convert("RGBA")
        elif img.mode == "LA":
            img = img.convert("RGBA")

    return img


def save_image(
    img: Image.Image,
    output_path: str,
    target_format: str,
    quality: int = 90,
) -> int:
    """保存图片，返回文件大小（字节）"""
    fmt = target_format.lower()
    if fmt == "jpeg":
        fmt = "jpg"

    save_params = {}

    if fmt == "jpg":
        save_params = {"quality": quality, "optimize": True}
    elif fmt == "webp":
        save_params = {"quality": quality, "method": 4}
    elif fmt == "png":
        save_params = {"optimize": True}

    img.save(output_path, format=_to_save_format(fmt), **save_params)
    return os.path.getsize(output_path)


def compress_to_target(
    img: Image.Image,
    output_path: str,
    target_format: str,
    target_kb: float,
    start_quality: int = 90,
    min_quality: Optional[int] = None,
) -> Tuple[int, Optional[str], int]:
    """
    压缩图片到目标大小
    返回 (最终文件大小字节, warning信息, 实际使用的quality)
    """
    if min_quality is None:
        min_quality = _get_min_quality(target_format)

    quality = start_quality
    warning = None

    while quality >= min_quality:
        file_size = save_image(img, output_path, target_format, quality)
        file_size_kb = file_size / 1024

        if file_size_kb <= target_kb:
            return file_size, None, quality

        quality -= QUALITY_STEP

    # 用最低质量保存，不再继续降低
    final_quality = min_quality
    file_size = save_image(img, output_path, target_format, final_quality)
    file_size_kb = file_size / 1024

    if file_size_kb > target_kb:
        warning = "COMPRESSION_TARGET_NOT_REACHED"

    return file_size, warning, final_quality


def process_image(
    input_path: str,
    original_filename: str,
    plan: Dict[str, Any],
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    """
    图片处理主流程

    处理顺序：
    1. 读取图片
    2. 修正 EXIF 方向
    3. resize / crop
    4. 转换格式
    5. 压缩
    6. 保存
    7. 返回结果
    """
    try:
        # 1. 读取图片
        with Image.open(input_path) as img:
            original_format = img.format or os.path.splitext(original_filename)[1].upper().lstrip(".")
            original_size = os.path.getsize(input_path)
            original_info = {
                "filename": original_filename,
                "format": original_format.upper(),
                "width": img.width,
                "height": img.height,
                "file_size_kb": round(original_size / 1024, 2),
            }

            # 2. 修正 EXIF 方向
            img = fix_exif_orientation(img)

            # 确保图片是可处理的模式
            if img.mode == "P":
                img = img.convert("RGBA")

            # 3. resize / crop（原图转换模式下跳过 resize）
            crop_params = plan.get("crop", {})
            resize_params = plan.get("resize", {})
            compress_params = plan.get("compress", {})
            compress_mode = compress_params.get("compress_mode", "lossy")

            if compress_mode == "none":
                # 原图转换模式：不裁剪、不缩放
                crop_params = {}
                resize_params = {}

            if crop_params:
                img = crop_image(img, crop_params)
            elif resize_params:
                img = resize_image(img, resize_params)

            # 4. 确定输出格式
            convert_params = plan.get("convert", {})
            target_fmt = output_format or convert_params.get("format", None)
            if not target_fmt:
                # 默认保持原格式
                fmt_map = {"JPEG": "jpg", "JPG": "jpg", "PNG": "png", "WEBP": "webp", "BMP": "png", "TIFF": "png"}
                target_fmt = fmt_map.get(original_format.upper(), "png")

            target_fmt = target_fmt.lower()
            if target_fmt == "jpeg":
                target_fmt = "jpg"

            # 5. 格式转换（处理颜色模式）
            img = convert_format(img, target_fmt)

            # 6. 压缩并保存
            warning = None
            warnings = []

            output_filename = generate_output_filename(original_filename, target_fmt)
            output_path = str(OUTPUT_DIR / output_filename)

            # 不压缩模式：仅格式转换，quality=100，不 resize
            if compress_mode == "none":
                quality_used = 100
                file_size = save_image(img, output_path, target_fmt, quality_used)
            else:
                quality = compress_params.get("quality", _get_default_quality(target_fmt))
                target_kb = compress_params.get("target_kb", None)
                quality_used = quality
                if target_kb is not None:
                    file_size, warning, quality_used = compress_to_target(
                        img, output_path, target_fmt, target_kb, start_quality=quality
                    )
                    if warning:
                        warnings.append(warning)
                else:
                    file_size = save_image(img, output_path, target_fmt, quality)

            file_size_kb = round(file_size / 1024, 2)
            target_kb = compress_params.get("target_kb", None)
            size_target_reached = target_kb is None or file_size_kb <= target_kb

            # 7. 返回结果
            result = {
                "success": True,
                "message": "Image processed successfully / 图片处理成功",
                "original": original_info,
                "processed": {
                    "filename": output_filename,
                    "format": _to_save_format(target_fmt),
                    "width": img.width,
                    "height": img.height,
                    "file_size_kb": file_size_kb,
                    "download_url": f"/download/{output_filename}",
                    "preview_url": f"/download/{output_filename}",
                    "quality_used": quality_used,
                    "compress_mode": compress_mode,
                    "target_kb": target_kb,
                    "final_file_size_kb": file_size_kb,
                    "size_target_reached": size_target_reached,
                    "warnings": warnings,
                },
                "operation_plan": {
                    "resize": resize_params if resize_params else {},
                    "crop": crop_params if crop_params else {},
                    "convert": convert_params if convert_params else {},
                    "compress": compress_params if compress_params else {},
                },
            }

            if warning:
                result["warning"] = warning
                result["message"] = (
                    "The target file size could not be reached without reducing image quality too much. "
                    "/ 在不明显损失画质的情况下，无法达到目标文件大小。"
                )

            return result

    except Exception as e:
        return {
            "success": False,
            "error_code": "PROCESSING_ERROR",
            "message": f"Image processing failed / 图片处理失败: {str(e)}",
            "suggestion": "Please check the image file and try again / 请检查图片文件后重试",
        }


def check_format_supported(filename: str) -> bool:
    """检查文件格式是否支持"""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext in SUPPORTED_INPUT_FORMATS
