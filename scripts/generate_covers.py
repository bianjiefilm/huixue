#!/usr/bin/env python3
"""
generate_covers.py - 为缺封面的实训项目生成带名字的纯色背景封面图片
"""
import os
import json
import random
import subprocess

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("正在安装 Pillow 库...")
    subprocess.check_call(["pip3", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

TRAINING_DIR = '/data/huixue_storage/static/ziyuan_data_full/实训资源'

# 定义几种深邃、极简风格的背景颜色配置
PALETTES = [
    {"bg": "#1e3a8a", "text": "#ffffff"}, # 深蓝 / 白
    {"bg": "#111827", "text": "#f3f4f6"}, # 极黑 / 银
    {"bg": "#0f766e", "text": "#ffffff"}, # 深青 / 白
    {"bg": "#4338ca", "text": "#e0e7ff"}, # 靛蓝 / 浅蓝
    {"bg": "#831843", "text": "#fbcfe8"}, # 深红 / 粉
]

def generate_cover(filename, text):
    """生成带文本的 600x400 图片并保存到 filename"""
    width, height = 600, 400
    palette = random.choice(PALETTES)
    
    # 1. 创建纯色背景图
    img = Image.new('RGB', (width, height), color=palette["bg"])
    draw = ImageDraw.Draw(img)
    
    # 2. 尝试加载支持中文的字体，若没有则回退到默认
    # 在 Ubuntu 容器中寻找常见中文字体
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
    ]
    
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, size=48)
                break
            except IOError:
                pass
                
    if font is None:
         # 实在找不到字体的话... 可能会乱码，尝试下载一个默认开源字体
         if not os.path.exists('/tmp/NotoSansSC-Regular.ttf'):
             print(">> 正在下载临时中文字体...")
             subprocess.call(['wget', '-q', '-O', '/tmp/NotoSansSC-Regular.ttf', 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf'])
         if os.path.exists('/tmp/NotoSansSC-Regular.ttf'):
             font = ImageFont.truetype('/tmp/NotoSansSC-Regular.ttf', size=48)
         else:
             font = ImageFont.load_default()
    
    # 3. 字体换行处理。一行最多10个字符
    chars_per_line = 10
    lines = []
    for i in range(0, len(text), chars_per_line):
        lines.append(text[i:i+chars_per_line])
        
    combined_text = "\n".join(lines)
        
    # 4. 计算文本居中并绘制
    # getbbox returns (left, top, right, bottom)
    bbox = draw.textbbox((0, 0), combined_text, font=font, align="center")
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (width - text_w) / 2
    y = (height - text_h) / 2
    
    draw.text((x, y), combined_text, font=font, fill=palette["text"], align="center")
    
    # 5. 存储
    try:
        img.save(filename)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

def main():
    print("="*50)
    print("开始生成缺失的实训封面图 (14个黄牌报警)")
    print("="*50)
    
    if not os.path.exists(TRAINING_DIR):
        print(f"错误: 目录不存在 {TRAINING_DIR}")
        return
        
    folders = [f for f in os.listdir(TRAINING_DIR) 
              if os.path.isdir(os.path.join(TRAINING_DIR, f)) and not f.startswith('.')]
    
    generated_count = 0
    for folder in sorted(folders):
        folder_path = os.path.join(TRAINING_DIR, folder)
        cover_path = os.path.join(folder_path, 'cover.png')
        
        # 如果没有 cover.png
        if not os.path.exists(cover_path):
            title = folder
            meta_path = os.path.join(folder_path, 'metadata.json')
            if os.path.exists(meta_path):
                 try:
                     with open(meta_path, 'r', encoding='utf-8') as f:
                         meta = json.load(f)
                         title = meta.get('title', folder)
                 except:
                     pass
                     
            print(f"[{folder}] 发现缺失，正在为它生成: {title[:15]}...")
            ok = generate_cover(cover_path, title)
            if ok:
                generated_count += 1
                print("  => 成功")
            else:
                print("  => 失败")
                
    print("\n" + "="*50)             
    print(f"完成！共为 {generated_count} 个缺失项生成了封面。前端黄牌警告已消除。")

if __name__ == '__main__':
    main()
