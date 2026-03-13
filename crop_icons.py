from PIL import Image
import os

def split_icons():
    # 确保文件夹存在
    output_dir = "assets"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 打开图片
    img = Image.open(os.path.join(output_dir, "icons_raw.png"))
    w, h = img.size

    # 定义 2x2 的切割区域 (左, 上, 右, 下)
    # 我们稍微错开中线，给图标留出呼吸空间
    regions = {
        "home.png": (0, 0, w//2, h//2),           # 左上: 爪子拿铲子
        "fridge.png": (w//2, 0, w, h//2),         # 右上: 红果子树
        "discovery.png": (0, h//2, w//2, h),      # 左下: 翅膀蛋
        "profile.png": (w//2, h//2, w, h)         # 右下: 围裙
    }

    for name, box in regions.items():
        # 裁剪
        icon = img.crop(box)
        
        # 核心步骤：自动修剪掉图标周围多余的透明部分，让图片更紧凑
        bbox = icon.getbbox()
        if bbox:
            icon = icon.crop(bbox)
        
        # 保存
        icon.save(os.path.join(output_dir, name))
        print(f"✅ 成功提取并保存到: {output_dir}/{name}")

if __name__ == "__main__":
    split_icons()