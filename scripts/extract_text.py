#!/usr/bin/env python3
"""从SRT字幕文件提取纯文本"""

import sys
import re
import argparse
from pathlib import Path


def extract_text_from_srt(srt_path: str) -> str:
    """从SRT文件提取纯文本"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')
    text_lines = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 跳过空行
        if not line:
            i += 1
            continue

        # 跳过序号（纯数字行）
        if line.isdigit():
            i += 1
            continue

        # 跳过时间戳行（包含 -->）
        if '-->' in line:
            i += 1
            continue

        # 这是文本行
        text_lines.append(line)
        i += 1

    return '\n'.join(text_lines)


def count_subtitle_stats(srt_path: str) -> dict:
    """统计字幕基本信息"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计行数（非空、非时间戳行）
    lines = content.strip().split('\n')
    text_count = 0
    for line in lines:
        line = line.strip()
        if line and not line.isdigit() and '-->' not in line:
            text_count += 1

    # 提取纯文本
    text = extract_text_from_srt(srt_path)
    char_count = len(text)
    word_count = len(text.replace('\n', '').split())

    return {
        'text_lines': text_count,
        'characters': char_count,
        'words': word_count
    }


def main():
    parser = argparse.ArgumentParser(description='从SRT字幕提取纯文本')
    parser.add_argument('input', help='SRT文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认stdout）')

    args = parser.parse_args()

    text = extract_text_from_srt(args.input)
    stats = count_subtitle_stats(args.input)

    output = f"""# 字幕纯文本

## 统计信息
- 字幕行数: {stats['text_lines']}
- 字符数: {stats['characters']}
- 词数: {stats['words']}

---

{text}
"""

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"[OK] 已保存到: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
