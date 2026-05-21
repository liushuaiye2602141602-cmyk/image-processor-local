"""
command_parser.py - 一句话指令解析器
支持中文和英文自然语言指令
"""
import re
from typing import Dict, Any, Optional


def parse_instruction(text: str) -> Dict[str, Any]:
    """
    解析一句话图片处理指令，返回结构化的操作参数
    """
    text = text.strip()
    if not text:
        return _default_plan()

    plan = _default_plan()
    text_lower = text.lower()

    # 检测预设
    preset = _detect_preset(text_lower)
    if preset:
        return preset

    # 解析裁剪
    crop = _parse_crop(text_lower)
    if crop:
        plan["crop"] = crop
        # 裁剪时也可以有格式转换和压缩
        _parse_format_and_compress(text_lower, plan)
        return plan

    # 解析指定尺寸
    exact_size = _parse_exact_size(text_lower)
    if exact_size:
        plan["resize"] = exact_size

    # 解析宽度缩放
    if not plan["resize"]:
        width = _parse_width(text_lower)
        if width:
            plan["resize"] = {"mode": "width", "width": width}

    # 解析高度缩放
    if not plan["resize"]:
        height = _parse_height(text_lower)
        if height:
            plan["resize"] = {"mode": "height", "height": height}

    # 解析保持原尺寸
    if _parse_no_resize(text_lower):
        plan["resize"] = {"mode": "none"}

    # 解析格式转换和压缩
    _parse_format_and_compress(text_lower, plan)

    return plan


def _default_plan() -> Dict[str, Any]:
    return {
        "resize": {},
        "crop": {},
        "convert": {},
        "compress": {},
    }


def _detect_preset(text: str) -> Optional[Dict[str, Any]]:
    """检测常用预设"""
    # 独立站产品主图
    if re.search(r'独立站产品主图|产品主图|网站产品图|website\s*product\s*image', text):
        return {
            "resize": {"mode": "exact", "width": 1000, "height": 1000, "pad": True},
            "crop": {},
            "convert": {"format": "webp"},
            "compress": {"quality": 88},
        }

    # 博客配图
    if re.search(r'博客配图|文章配图|blog\s*image', text):
        return {
            "resize": {"mode": "exact", "width": 1200, "height": 800, "pad": True},
            "crop": {},
            "convert": {"format": "webp"},
            "compress": {"quality": 88},
        }

    # 网站 Banner
    if re.search(r'网站\s*banner|网站横幅|banner\s*image', text):
        return {
            "resize": {"mode": "exact", "width": 1200, "height": 600, "pad": True},
            "crop": {},
            "convert": {"format": "webp"},
            "compress": {"quality": 88},
        }

    # LinkedIn 方图
    if re.search(r'linkedin\s*方图|领英方图|linkedin\s*square', text):
        return {
            "resize": {"mode": "exact", "width": 1080, "height": 1080, "pad": True},
            "crop": {},
            "convert": {"format": "webp"},
            "compress": {"quality": 88},
        }

    # Instagram 竖图
    if re.search(r'instagram\s*竖图|ig\s*竖图|instagram\s*portrait', text):
        return {
            "resize": {"mode": "exact", "width": 1080, "height": 1350, "pad": True},
            "crop": {},
            "convert": {"format": "webp"},
            "compress": {"quality": 88},
        }

    return None


def _parse_crop(text: str) -> Optional[Dict[str, Any]]:
    """解析裁剪指令"""
    patterns = [
        r'裁剪[成为]?\s*(\d+)\s*[x×]\s*(\d+)',
        r'裁剪为\s*(\d+)\s*[x×]\s*(\d+)',
        r'中心裁剪\s*(\d+)\s*[x×]\s*(\d+)',
        r'crop\s+to\s+(\d+)\s*[x×]\s*(\d+)',
        r'center\s+crop\s+(\d+)\s*[x×]\s*(\d+)',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return {"mode": "center", "width": int(m.group(1)), "height": int(m.group(2))}
    return None


def _parse_exact_size(text: str) -> Optional[Dict[str, Any]]:
    """解析指定尺寸"""
    patterns = [
        r'改成\s*(\d+)\s*[x×]\s*(\d+)',
        r'调整为\s*(\d+)\s*[x×]\s*(\d+)',
        r'尺寸改成\s*(\d+)\s*[x×]\s*(\d+)',
        r'resize\s+to\s+(\d+)\s*[x×]\s*(\d+)',
        r'^(\d+)\s*[x×]\s*(\d+)$',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            # 检查是否拉伸
            stretch = bool(re.search(r'拉伸|强制拉伸|stretch', text))
            return {
                "mode": "exact",
                "width": w,
                "height": h,
                "stretch": stretch,
                "pad": not stretch,
            }
    return None


def _parse_width(text: str) -> Optional[int]:
    """解析宽度缩放"""
    patterns = [
        r'宽度?\s*(?:改成|调整为)?\s*(\d+)\s*px',
        r'宽\s*(?:改成|调整为)?\s*(\d+)\s*px',
        r'width\s+(\d+)\s*px',
        r'resize\s+width\s+to\s+(\d+)\s*px',
        r'^w\s+(\d+)\s*px$',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return int(m.group(1))
    return None


def _parse_height(text: str) -> Optional[int]:
    """解析高度缩放"""
    patterns = [
        r'高度?\s*(?:改成|调整为)?\s*(\d+)\s*px',
        r'高\s*(?:改成|调整为)?\s*(\d+)\s*px',
        r'height\s+(\d+)\s*px',
        r'resize\s+height\s+to\s+(\d+)\s*px',
        r'^h\s+(\d+)\s*px$',
    ]
    for pattern in patterns:
        m = re.search(pattern, text)
        if m:
            return int(m.group(1))
    return None


def _parse_no_resize(text: str) -> bool:
    """检测是否保持原尺寸"""
    patterns = [
        r'不改尺寸', r'保持原尺寸', r'尺寸不变',
        r'no\s*resize', r'keep\s*original\s*size',
    ]
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def _parse_format_and_compress(text_lower: str, plan: Dict[str, Any]):
    """解析格式转换和压缩"""
    # 格式转换（使用 text_lower 统一小写匹配，避免 WebP/webp/WEBP 混合大小写问题）
    if re.search(r'转[成为]?\s*webp|输出\s*webp|保存为\s*webp|convert\s+to\s+webp|save\s+as\s+webp', text_lower):
        plan["convert"] = {"format": "webp"}
    elif re.search(r'转[成为]?\s*(?:jpg|jpeg)|输出\s*(?:jpg|jpeg)|保存为\s*(?:jpg|jpeg)|convert\s+to\s*(?:jpg|jpeg)|save\s+as\s*(?:jpg|jpeg)', text_lower):
        plan["convert"] = {"format": "jpg"}
    elif re.search(r'转[成为]?\s*png|输出\s*png|保存为\s*png|convert\s+to\s+png|save\s+as\s+png', text_lower):
        plan["convert"] = {"format": "png"}

    # 压缩到指定大小
    compress_info = {}

    # KB 单位
    size_match = re.search(r'压缩到?\s*(\d+)\s*kb\s*(?:以内|以下)?', text_lower)
    if not size_match:
        size_match = re.search(r'小于\s*(\d+)\s*kb', text_lower)
    if not size_match:
        size_match = re.search(r'不超过\s*(\d+)\s*kb', text_lower)
    if not size_match:
        size_match = re.search(r'compress\s+(?:under|to)\s+(\d+)\s*kb', text_lower)
    if not size_match:
        size_match = re.search(r'less\s+than\s+(\d+)\s*kb', text_lower)
    if not size_match:
        size_match = re.search(r'under\s+(\d+)\s*kb', text_lower)

    # MB 单位
    if not size_match:
        size_match = re.search(r'压缩到?\s*(\d+)\s*mb\s*(?:以内|以下)?', text_lower)
        if size_match:
            compress_info["target_kb"] = int(size_match.group(1)) * 1024
    if not size_match:
        size_match = re.search(r'小于\s*(\d+)\s*mb', text_lower)
        if size_match:
            compress_info["target_kb"] = int(size_match.group(1)) * 1024
    if not size_match:
        size_match = re.search(r'compress\s+(?:under|to)\s+(\d+)\s*mb', text_lower)
        if size_match:
            compress_info["target_kb"] = int(size_match.group(1)) * 1024
    if not size_match:
        size_match = re.search(r'less\s+than\s+(\d+)\s*mb', text_lower)
        if size_match:
            compress_info["target_kb"] = int(size_match.group(1)) * 1024
    if not size_match:
        size_match = re.search(r'under\s+(\d+)\s*mb', text_lower)
        if size_match:
            compress_info["target_kb"] = int(size_match.group(1)) * 1024

    if "target_kb" not in compress_info and size_match:
        compress_info["target_kb"] = int(size_match.group(1))

    # 质量参数
    quality_match = re.search(r'质量\s*(\d+)', text_lower)
    if not quality_match:
        quality_match = re.search(r'图片质量\s*(\d+)', text_lower)
    if not quality_match:
        quality_match = re.search(r'quality\s+(\d+)', text_lower)
    if not quality_match:
        quality_match = re.search(r'set\s+quality\s+(\d+)', text_lower)

    if quality_match:
        q = int(quality_match.group(1))
        compress_info["quality"] = max(72, min(100, q))

    # 通用压缩关键词（不指定质量时，由 image_utils 根据输出格式选择默认质量）
    if not compress_info and re.search(r'压缩|compress', text_lower):
        pass  # 不设置 quality，让 process_image 根据格式使用 WEBP_DEFAULT_QUALITY 或 JPEG_DEFAULT_QUALITY

    if compress_info:
        plan["compress"] = compress_info
