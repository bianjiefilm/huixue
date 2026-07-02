#!/bin/bash
# 批量转换视频为Web兼容格式的脚本
# 使用 H.264 Main Profile Level 3.1，确保浏览器兼容性

RESOURCE_DIR="/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源"
BACKUP_DIR="/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源_原始备份"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 计数器
total=0
converted=0
failed=0

echo "=========================================="
echo "视频批量转码脚本 - Web兼容格式"
echo "=========================================="
echo ""

# 查找所有 mp4 文件
while IFS= read -r -d '' file; do
    total=$((total + 1))
    filename=$(basename "$file")
    dirname=$(dirname "$file")
    relative_path="${file#$RESOURCE_DIR/}"

    echo "[$total] 处理: $relative_path"

    # 检查是否已经是兼容格式（检查 profile）
    profile=$(ffprobe -v error -select_streams v:0 -show_entries stream=profile -of csv=p=0 "$file" 2>/dev/null)

    if [[ "$profile" == "Main" || "$profile" == "Baseline" ]]; then
        echo "    ✓ 已是兼容格式，跳过"
        continue
    fi

    # 创建备份子目录结构
    backup_subdir="$BACKUP_DIR/$(dirname "$relative_path")"
    mkdir -p "$backup_subdir"

    # 备份原文件
    if [[ ! -f "$BACKUP_DIR/$relative_path" ]]; then
        echo "    → 备份原文件..."
        cp "$file" "$BACKUP_DIR/$relative_path"
    fi

    # 转码
    temp_file="${file%.mp4}_temp.mp4"
    echo "    → 转码中..."

    if ffmpeg -y -i "$file" \
        -c:v libx264 -profile:v main -level 3.1 \
        -preset medium -crf 20 \
        -c:a aac -b:a 128k \
        -movflags +faststart \
        "$temp_file" 2>/dev/null; then

        # 替换原文件
        mv "$temp_file" "$file"
        converted=$((converted + 1))
        echo "    ✓ 转码完成"
    else
        failed=$((failed + 1))
        rm -f "$temp_file"
        echo "    ✗ 转码失败"
    fi

    echo ""
done < <(find "$RESOURCE_DIR" -name "*.mp4" -type f -print0)

echo "=========================================="
echo "转码完成!"
echo "总计: $total 个视频"
echo "转码: $converted 个"
echo "失败: $failed 个"
echo "原文件已备份到: $BACKUP_DIR"
echo "=========================================="
