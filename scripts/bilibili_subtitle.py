#!/usr/bin/env python3
"""从B站API直接获取AI字幕

背景：yt-dlp 和 /x/player/v2 接口经常拿不到B站AI字幕，
但 /x/v2/dm/view 接口可以返回字幕URL。
此脚本通过B站API直接获取字幕，绕过yt-dlp的限制。
"""

import sys
import io
import json
import argparse
from pathlib import Path

# Windows 编码问题修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import requests
except ImportError:
    print("[ERROR] 需要安装 requests: pip install requests")
    sys.exit(1)


def find_cookie_file():
    """按优先级查找Cookie文件"""
    search_paths = [
        Path("bilibili_cookies.txt"),
        Path(__file__).parent.parent / "bilibili_cookies.txt",
        Path.home() / "bilibili_cookies.txt",
    ]
    for p in search_paths:
        if p.exists():
            return str(p)
    return None


def parse_sessdata(cookie_path):
    """从Cookie文件中提取SESSDATA"""
    with open(cookie_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 7 and parts[-2] == 'SESSDATA':
                return parts[-1]
    return None


def get_video_info(bvid, headers):
    """获取视频基本信息（cid, aid, title等）"""
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data['code'] != 0:
        raise RuntimeError(f"API error: {data.get('message', 'unknown')}")
    info = data['data']
    return {
        'cid': info['cid'],
        'aid': info['aid'],
        'title': info['title'],
        'duration': info['duration'],
        'owner': info['owner']['name'],
        'desc': info['desc'],
        'view': info['stat']['view'],
    }


def get_subtitle_url(cid, aid, headers):
    """通过 /x/v2/dm/view 接口获取AI字幕URL"""
    url = f"https://api.bilibili.com/x/v2/dm/view?oid={cid}&type=1&pid={aid}"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data['code'] != 0:
        raise RuntimeError(f"DM API error: {data.get('message', 'unknown')}")

    subtitle_info = data.get('data', {}).get('subtitle', {})
    subtitles = subtitle_info.get('subtitles', [])

    if not subtitles:
        return None, None

    # 优先 ai-zh，其次任何中文字幕
    for sub in subtitles:
        if sub.get('lan') == 'ai-zh':
            return sub['subtitle_url'], sub.get('lan_doc', '')

    # fallback: 取第一个
    return subtitles[0]['subtitle_url'], subtitles[0].get('lan_doc', '')


def download_subtitle(subtitle_url, output_path=None):
    """下载字幕JSON并提取纯文本"""
    # 确保使用http
    if subtitle_url.startswith('//'):
        subtitle_url = 'http:' + subtitle_url
    elif subtitle_url.startswith('https://'):
        subtitle_url = 'http://' + subtitle_url[8:]

    resp = requests.get(subtitle_url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    body = data.get('body', [])
    if not body:
        return None, 0

    # 提取纯文本
    text_lines = []
    for item in body:
        content = item.get('content', '').strip()
        if content:
            text_lines.append(content)

    full_text = ''.join(text_lines)

    # 保存原始JSON（可选）
    if output_path:
        json_path = str(output_path).replace('.txt', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存纯文本
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

    return full_text, len(body)


def main():
    parser = argparse.ArgumentParser(
        description='[OK] B站AI字幕提取工具（直接调用B站API）'
    )
    parser.add_argument('bvid', help='视频BV号（如 BV1DCDjBRExV）')
    parser.add_argument('-o', '--output', help='输出文件路径（默认stdout）')
    parser.add_argument('--cookie', help='Cookie文件路径')
    parser.add_argument('--preview', type=int, default=0,
                        help='预览模式：只输出前N个字符')
    parser.add_argument('--info', action='store_true',
                        help='仅显示视频信息，不下载字幕')

    args = parser.parse_args()

    # 提取BV号
    bvid = args.bvid
    if 'bilibili.com' in bvid:
        # 从URL中提取BV号
        import re
        match = re.search(r'(BV[\w]+)', bvid)
        if match:
            bvid = match.group(1)
        else:
            print("[ERROR] 无法从URL中提取BV号")
            sys.exit(1)

    # 查找Cookie
    cookie_path = args.cookie or find_cookie_file()
    if not cookie_path:
        print("[ERROR] 未找到Cookie文件，请提供 --cookie 参数")
        sys.exit(1)

    sessdata = parse_sessdata(cookie_path)
    if not sessdata:
        print("[ERROR] Cookie文件中未找到SESSDATA")
        sys.exit(1)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
        'Cookie': f'SESSDATA={sessdata}'
    }

    # Step 1: 获取视频信息
    print(f"[INFO] 正在获取视频信息: {bvid}")
    info = get_video_info(bvid, headers)
    print(f"[INFO] 标题: {info['title']}")
    print(f"[INFO] UP主: {info['owner']}")
    print(f"[INFO] 时长: {info['duration']}秒")

    if args.info:
        print(f"[INFO] cid: {info['cid']}, aid: {info['aid']}")
        return

    # Step 2: 获取字幕URL
    print(f"[INFO] 正在获取AI字幕...")
    subtitle_url, lang_doc = get_subtitle_url(info['cid'], info['aid'], headers)

    if not subtitle_url:
        print("[WARN] 该视频没有AI字幕")
        # 尝试yt-dlp作为fallback
        print("[INFO] 可尝试: yt-dlp --cookies <cookie> --list-subs <URL>")
        sys.exit(1)

    print(f"[INFO] 找到字幕: {lang_doc}")

    # Step 3: 下载字幕
    output_path = args.output
    if output_path is None and not args.preview:
        output_path = f"subtitle_{bvid}.txt"

    text, count = download_subtitle(subtitle_url, output_path)

    if not text:
        print("[ERROR] 字幕内容为空")
        sys.exit(1)

    print(f"[INFO] 字幕条数: {count}, 字符数: {len(text)}")

    if args.preview > 0:
        print(f"[INFO] 预览前 {args.preview} 字符:")
        print("-" * 40)
        print(text[:args.preview])
    elif output_path:
        print(f"[OK] 已保存到: {output_path}")
    else:
        print(text)


if __name__ == '__main__':
    main()
