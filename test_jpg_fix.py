"""
test_jpg_fix.py - 验证 JPG/JPEG 格式修复
测试所有 JPG 相关场景
"""
import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
from app.image_utils import (
    process_image, save_image, convert_format, _to_save_format,
    OUTPUT_DIR, SUPPORTED_INPUT_FORMATS
)
from app.command_parser import parse_instruction


def create_test_images():
    """创建测试图片"""
    test_dir = Path(__file__).parent / "test_images"
    test_dir.mkdir(exist_ok=True)

    # 1. 普通 RGB PNG
    img_rgb = Image.new("RGB", (200, 200), (255, 0, 0))
    img_rgb.save(str(test_dir / "test_rgb.png"), format="PNG")

    # 2. 带透明通道的 RGBA PNG
    img_rgba = Image.new("RGBA", (200, 200), (255, 0, 0, 128))
    img_rgba.save(str(test_dir / "test_rgba.png"), format="PNG")

    # 3. 普通 JPG
    img_jpg = Image.new("RGB", (200, 200), (0, 255, 0))
    img_jpg.save(str(test_dir / "test.jpg"), format="JPEG")

    # 4. WebP
    img_webp = Image.new("RGB", (200, 200), (0, 0, 255))
    img_webp.save(str(test_dir / "test.webp"), format="WEBP")

    # 5. 带透明通道的 WebP
    img_webp_rgba = Image.new("RGBA", (200, 200), (0, 0, 255, 128))
    img_webp_rgba.save(str(test_dir / "test_rgba.webp"), format="WEBP")

    # 6. Palette 模式 PNG
    img_p = Image.new("P", (200, 200))
    img_p.save(str(test_dir / "test_palette.png"), format="PNG")

    print(f"Test images created in: {test_dir}")
    return test_dir


def test_normalize_format():
    """测试格式标准化函数"""
    print("\n=== Test: _to_save_format ===")
    cases = {
        "jpg": "JPEG", "JPG": "JPEG", "jpeg": "JPEG", "JPEG": "JPEG",
        "png": "PNG", "PNG": "PNG",
        "webp": "WEBP", "WebP": "WEBP",
        "bmp": "BMP", "BMP": "BMP",
        "tif": "TIFF", "tiff": "TIFF", "TIFF": "TIFF",
    }
    all_pass = True
    for input_fmt, expected in cases.items():
        result = _to_save_format(input_fmt)
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  _to_save_format('{input_fmt}') = '{result}' (expected '{expected}') [{status}]")
    return all_pass


def test_png_to_jpg(test_dir):
    """测试 PNG 转 JPG"""
    print("\n=== Test: PNG → JPG ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test_rgb.png"), "test_rgb.png", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    print(f"  PNG → JPG: PASS (file: {result['processed']['filename']})")
    return True


def test_png_to_jpeg_label(test_dir):
    """测试 PNG 转 JPEG（指令写 JPEG）"""
    print("\n=== Test: PNG → JPEG (via instruction) ===")
    plan = parse_instruction("convert to JPEG")
    result = process_image(str(test_dir / "test_rgb.png"), "test_rgb.png", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    assert result["processed"]["filename"].endswith(".jpg"), f"Wrong ext: {result['processed']['filename']}"
    print(f"  PNG → JPEG: PASS (file: {result['processed']['filename']})")
    return True


def test_jpg_to_webp(test_dir):
    """测试 JPG 转 WebP"""
    print("\n=== Test: JPG → WebP ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "webp"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test.jpg"), "test.jpg", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "WEBP", f"Wrong format: {result['processed']['format']}"
    print(f"  JPG → WebP: PASS (file: {result['processed']['filename']})")
    return True


def test_webp_to_jpg(test_dir):
    """测试 WebP 转 JPG"""
    print("\n=== Test: WebP → JPG ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test.webp"), "test.webp", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    print(f"  WebP → JPG: PASS (file: {result['processed']['filename']})")
    return True


def test_rgba_png_to_jpg(test_dir):
    """测试带透明通道的 PNG 转 JPG"""
    print("\n=== Test: RGBA PNG → JPG (透明背景→白底) ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test_rgba.png"), "test_rgba.png", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    # 验证输出图片是 RGB 模式（不带透明通道）
    output_path = str(OUTPUT_DIR / result["processed"]["filename"])
    with Image.open(output_path) as out_img:
        assert out_img.mode == "RGB", f"Wrong mode: {out_img.mode}"
    print(f"  RGBA PNG → JPG: PASS (mode=RGB, file: {result['processed']['filename']})")
    return True


def test_rgba_webp_to_jpg(test_dir):
    """测试带透明通道的 WebP 转 JPG"""
    print("\n=== Test: RGBA WebP → JPG (透明背景→白底) ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test_rgba.webp"), "test_rgba.webp", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    output_path = str(OUTPUT_DIR / result["processed"]["filename"])
    with Image.open(output_path) as out_img:
        assert out_img.mode == "RGB", f"Wrong mode: {out_img.mode}"
    print(f"  RGBA WebP → JPG: PASS (mode=RGB, file: {result['processed']['filename']})")
    return True


def test_all_jpg_input_variants(test_dir):
    """测试指令中各种 JPG/JPEG 写法"""
    print("\n=== Test: 各种 JPG/JPEG 指令写法 ===")
    instructions = [
        "转成JPG", "转成jpg", "转成JPEG", "转成jpeg",
        "convert to JPG", "convert to jpg", "convert to JPEG", "convert to jpeg",
        "save as JPG", "save as jpg", "save as JPEG", "save as jpeg",
        "输出jpg", "输出jpeg",
    ]
    all_pass = True
    for inst in instructions:
        plan = parse_instruction(inst)
        fmt = plan.get("convert", {}).get("format", "NONE")
        if fmt != "jpg":
            print(f"  '{inst}' → format='{fmt}' [FAIL, expected 'jpg']")
            all_pass = False
            continue
        result = process_image(str(test_dir / "test_rgb.png"), "test_rgb.png", plan)
        if not result["success"]:
            print(f"  '{inst}' → processing failed: {result.get('message')} [FAIL]")
            all_pass = False
            continue
        if result["processed"]["format"] != "JPEG":
            print(f"  '{inst}' → output format='{result['processed']['format']}' [FAIL, expected 'JPEG']")
            all_pass = False
            continue
        print(f"  '{inst}' → JPEG [PASS]")
    return all_pass


def test_original_mode_jpg(test_dir):
    """测试原图转换模式下 JPG"""
    print("\n=== Test: Original mode PNG → JPG ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "none"}}
    result = process_image(str(test_dir / "test_rgb.png"), "test_rgb.png", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["quality_used"] == 100, f"Wrong quality: {result['processed']['quality_used']}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    print(f"  Original mode PNG → JPG: PASS (quality={result['processed']['quality_used']})")
    return True


def test_palette_png_to_jpg(test_dir):
    """测试 Palette 模式 PNG 转 JPG"""
    print("\n=== Test: Palette PNG → JPG ===")
    plan = {"resize": {}, "crop": {}, "convert": {"format": "jpg"}, "compress": {"compress_mode": "lossy", "quality": 90}}
    result = process_image(str(test_dir / "test_palette.png"), "test_palette.png", plan)
    assert result["success"], f"Failed: {result}"
    assert result["processed"]["format"] == "JPEG", f"Wrong format: {result['processed']['format']}"
    print(f"  Palette PNG → JPG: PASS (file: {result['processed']['filename']})")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("JPG/JPEG Format Fix - Test Suite")
    print("=" * 60)

    test_dir = create_test_images()
    results = []

    results.append(("格式标准化函数", test_normalize_format()))
    results.append(("PNG → JPG", test_png_to_jpg(test_dir)))
    results.append(("PNG → JPEG (指令)", test_png_to_jpeg_label(test_dir)))
    results.append(("JPG → WebP", test_jpg_to_webp(test_dir)))
    results.append(("WebP → JPG", test_webp_to_jpg(test_dir)))
    results.append(("RGBA PNG → JPG (白底)", test_rgba_png_to_jpg(test_dir)))
    results.append(("RGBA WebP → JPG (白底)", test_rgba_webp_to_jpg(test_dir)))
    results.append(("各种 JPG/JPEG 指令", test_all_jpg_input_variants(test_dir)))
    results.append(("Original mode JPG", test_original_mode_jpg(test_dir)))
    results.append(("Palette PNG → JPG", test_palette_png_to_jpg(test_dir)))

    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {name}: {status}")

    print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_pass else 1)
