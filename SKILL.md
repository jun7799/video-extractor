---
name: video-extractor
description: 视频字幕提取与内容解读工具。支持B站(av/BV)、YouTube等平台的视频字幕自动提取、文本总结，以及保存到飞书多维表格。当用户说"提取视频字幕"、"解读B站视频"、"分析YouTube视频"、"把视频做成文字总结"时使用此skill。自动识别视频平台，处理登录验证，提取AI字幕或弹幕，生成结构化内容总结。
compatibility: yt-dlp, Python, 飞书API(可选)
---

# Video Extractor Skill

从视频平台提取字幕并生成内容解读。

## 支持的平台

| 平台 | 视频ID格式 | 备注 |
|------|-----------|------|
| B站 | BVxxxxx, avxxxxx | 需要Cookie提取AI字幕 |
| YouTube | video_id | 支持自动字幕 |

## 工作流程

### 步骤1: 获取视频元数据

```bash
# 获取完整视频信息
yt-dlp --print "%(title)s|%(duration_string)s|%(uploader)s|%(upload_date)s|%(view_count)s" "<视频URL>" 2>/dev/null
```

### 步骤2: 检测平台并提取字幕

根据视频URL识别平台，使用对应工具提取字幕：

**YouTube视频（推荐流程）：**
```bash
# 1. 列出可用字幕
yt-dlp --list-subs "<视频URL>"

# 2. 按优先级下载字幕（自动 fallback）
# 优先级: zh-Hans > zh-Hant > en > en-orig
yt-dlp --write-auto-subs --sub-lang zh-Hans --convert-subs srt "<视频URL>" -o "subtitle" --skip-download

# 如果中文失败，fallback 到英文
yt-dlp --write-auto-subs --sub-lang en --convert-subs srt "<视频URL>" -o "subtitle" --skip-download
```

**B站视频（推荐：直接调API）：**

**重要**：`yt-dlp` 和 `/x/player/v2` 接口经常拿不到B站AI字幕，必须使用 `/x/v2/dm/view` 接口。

```bash
# 方式1（推荐）：使用内置脚本，自动完成全流程
python <skill_dir>/scripts/bilibili_subtitle.py BV1DCDjBRExV -o subtitle_text.txt

# 也可以传入完整URL，脚本会自动提取BV号
python <skill_dir>/scripts/bilibili_subtitle.py "https://www.bilibili.com/video/BV1DCDjBRExV" -o subtitle_text.txt

# 仅查看视频信息（不下载字幕）
python <skill_dir>/scripts/bilibili_subtitle.py BV1DCDjBRExV --info

# 预览前500字
python <skill_dir>/scripts/bilibili_subtitle.py BV1DCDjBRExV --preview 500

# 指定Cookie文件
python <skill_dir>/scripts/bilibili_subtitle.py BV1DCDjBRExV --cookie /path/to/bilibili_cookies.txt -o subtitle_text.txt
```

脚本工作原理：
1. 从 `api.bilibili.com/x/web-interface/view` 获取 cid、aid
2. 从 `api.bilibili.com/x/v2/dm/view` 获取AI字幕URL（此接口比 yt-dlp 用的 `/x/player/v2` 更可靠）
3. 下载字幕JSON，提取纯文本
4. 同时保存 `.json`（原始字幕）和 `.txt`（纯文本）

**方式2（fallback）：yt-dlp**
```bash
# 如果脚本失败，可尝试 yt-dlp（成功率较低）
yt-dlp --cookies <cookie文件> --write-subs --sub-lang ai-zh --convert-subs srt "<视频URL>" -o "subtitle"
```

### 步骤3: 处理字幕文件（含去重）

**重要**：YouTube自动生成的字幕有大量重复，必须去重处理。

使用内置脚本一键处理：
```bash
python <skill_dir>/scripts/extract_text.py subtitle.<lang>.srt -o subtitle_text.txt --dedupe
```

去重逻辑：
- 移除连续重复的短语（YouTube字幕特性）
- 合并断句
- 统计字符数和行数

### 步骤4: 生成内容总结

对提取的文本进行分析，生成结构化总结：
- 视频主题
- 核心内容/观点
- 关键要点（3-5条）
- 金句摘录
- 视频风格/来源

### 步骤5: 保存到飞书（可选）

如果用户要求保存到飞书：
1. 读取飞书配置（App ID, App Secret）
2. 调用飞书API创建记录
3. 包含：标题、URL、总结内容、关键词

## 一键执行脚本

对于 YouTube 视频，可以使用以下一键命令：

```bash
# 设置工作目录
cd <用户指定目录>

# 下载字幕（带 fallback）
yt-dlp --write-auto-subs --sub-lang zh-Hans --convert-subs srt "<URL>" -o "subtitle" --skip-download 2>&1 || \
yt-dlp --write-auto-subs --sub-lang en --convert-subs srt "<URL>" -o "subtitle" --skip-download 2>&1

# 提取纯文本（含去重）
python <skill_dir>/scripts/extract_text.py subtitle.*.srt -o subtitle_text.txt --dedupe
```

## Cookie管理

### B站Cookie格式

需要以下Cookie值创建Netscape格式的cookie文件：
- SESSDATA（登录会话）
- bili_jct（CSRF token）
- DedeUserID（用户ID）
- DedeUserID__ckMd5（用户ID MD5）

**Cookie文件格式：**
```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	TRUE	<过期时间>	SESSDATA	<值>
.bilibili.com	TRUE	/	TRUE	<过期时间>	bili_jct	<值>
...
```

### Cookie文件位置

默认查找顺序：
1. 当前目录 `bilibili_cookies.txt`
2. 技能目录 `./bilibili_cookies.txt`
3. 用户目录 `~/bilibili_cookies.txt`

## 错误处理

| 错误 | 解决方案 |
|------|---------|
| HTTP 429 (Too Many Requests) | 切换语言 fallback，等待后重试 |
| 无字幕可下载 | B站用API脚本重试；YouTube尝试自动字幕 |
| Cookie无效/过期 | 提示用户重新提供Cookie或更新SESSDATA |
| B站API返回空字幕 | yt-dlp fallback，或该视频确实无AI字幕 |
| 网络超时 | 重试3次，每次间隔5秒 |
| 视频不存在 | 提示检查视频URL |
| 字幕文件过大 | 分段处理，提取关键部分 |
| Windows编码乱码 | 脚本已内置UTF-8处理；yt-dlp用Python subprocess调用 |

## 输出格式

### 字幕文件
- `subtitle.<lang>.srt` - SRT格式字幕
- `subtitle_text.txt` - 纯文本（去重后）

### 内容总结
```markdown
# 视频内容总结

## 基本信息
| 项目 | 内容 |
|------|------|
| **平台** | YouTube/B站 |
| **视频ID** | xxx |
| **时长** | xx:xx |
| **标题** | xxx |

## 主题概述

## 核心内容

### 1. 主题一
### 2. 主题二
### 3. 主题三

## 关键要点
1. xxx
2. xxx
3. xxx

## 金句摘录
> "xxx"

## 总结
```

## 依赖

```bash
# 必需
pip install yt-dlp requests

# 可选（解决 YouTube 下载警告）
# 安装 deno 或 node.js
# Windows: winget install DenoLand.Deno
# Mac: brew install deno
```

## 已知问题与解决方案

### 1. B站 yt-dlp 拿不到AI字幕
**问题**：`yt-dlp --write-subs --sub-lang ai-zh` 和 `/x/player/v2` API 经常返回空字幕
**根因**：B站的AI字幕信息在 `/x/v2/dm/view` 接口中，不在 `/x/player/v2` 中，yt-dlp 用的是后者
**解决**：使用 `bilibili_subtitle.py` 脚本直接调 `/x/v2/dm/view` 接口获取字幕URL

### 2. YouTube 字幕重复
**问题**：YouTube 自动字幕每句话重复3次
**解决**：使用 `--dedupe` 参数去重

### 3. HTTP 429 错误
**问题**：请求过于频繁被限制
**解决**：自动 fallback 到其他语言

### 4. Windows 编码问题
**问题**：Python/yt-dlp 输出中文乱码
**解决**：脚本已内置 UTF-8 编码处理；yt-dlp 用 Python subprocess 调用并指定 encoding

### 5. 字幕文件过大
**问题**：长视频字幕超过读取限制
**解决**：分段预览，提取关键部分

## 扩展计划

- [ ] 支持抖音/西瓜视频
- [ ] 支持本地视频语音识别
- [ ] 支持多语言字幕翻译
- [ ] 一键生成解读视频（调用content-video-generator）
- [ ] 添加进度条显示
