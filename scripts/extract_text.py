#!/usr/bin/env python3
"""从SRT字幕文件提取纯文本（支持去重）"""

import sys
import io
import re
import argparse
from pathlib import Path

# Windows 编码问题修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def dedupe_text(text: str) -> str:
    """
    去除 YouTube 自动字幕的重复问题
    YouTube 字幕特点：每句话重复 2-3 次
    """
    # 方法1: 去除连续重复的短语（逗号分隔）
    # 例如: "hello world, hello world, hello world" -> "hello world"
    text = re.sub(r'(\b[^,，]+[,，]\s*)\1+', r'\1', text)

    # 方法2: 去除连续重复的完整句子
    # 例如: "hello world hello world" -> "hello world"
    words = text.split()
    if len(words) > 3:
        result = []
        i = 0
        while i < len(words):
            result.append(words[i])
            # 检查接下来是否有重复
            j = i + 1
            repeat_len = 1
            while j < len(words):
                # 检查是否是前面内容的重复
                chunk_start = max(0, i - repeat_len + 1)
                chunk = words[chunk_start:i+1]
                next_chunk = words[j:j+len(chunk)]
                if chunk == next_chunk and len(chunk) > 0:
                    j += len(chunk)
                    repeat_len += 1
                else:
                    break
            i = j if j > i + 1 else i + 1

        # 简化版：直接去重连续重复的词组
        text = ' '.join(result)

    return text


def extract_text_from_srt(srt_path: str, dedupe: bool = True) -> str:
    """从SRT文件提取纯文本"""
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')
    text_lines = []

    for line in lines:
        line = line.strip()

        # 跳过空行
        if not line:
            continue

        # 跳过序号（纯数字行）
        if line.isdigit():
            continue

        # 跳过时间戳行（包含 -->）
        if '-->' in line:
            continue

        # 这是文本行
        text_lines.append(line)

    # 合并所有文本
    full_text = ' '.join(text_lines)

    # 去重处理
    if dedupe:
        full_text = dedupe_text(full_text)

    return full_text


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
    text = extract_text_from_srt(srt_path, dedupe=True)
    char_count = len(text)
    word_count = len(text.split())

    return {
        'text_lines': text_count,
        'characters': char_count,
        'words': word_count
    }


def main():
    parser = argparse.ArgumentParser(description='[OK] SRT字幕提取纯文本工具')
    parser.add_argument('input', help='SRT文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认stdout）')
    parser.add_argument('--dedupe', action='store_true', default=True,
                        help='去除重复文本（默认开启）')
    parser.add_argument('--no-dedupe', action='store_true',
                        help='保留原始文本，不去重')
    parser.add_argument('--preview', type=int, default=0,
                        help='预览模式：只输出前N个字符')

    args = parser.parse_args()

    dedupe = not args.no_dedupe
    text = extract_text_from_srt(args.input, dedupe=dedupe)
    stats = count_subtitle_stats(args.input)

    # 预览模式
    if args.preview > 0:
        print(f"[INFO] 总字符数: {stats['characters']}")
        print(f"[INFO] 预览前 {args.preview} 字符:")
        print("-" * 40)
        print(text[:args.preview])
        return

    output = f"""# 字幕纯文本

## 统计信息
- 字幕行数: {stats['text_lines']}
- 字符数: {stats['characters']}
- 词数: {stats['words']}
- 去重: {'是' if dedupe else '否'}

---

{text}
"""

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"[OK] 已保存到: {args.output}")
        print(f"[INFO] 字符数: {stats['characters']}, 词数: {stats['words']}")
    else:
        print(output)


if __name__ == '__main__':
    main()
