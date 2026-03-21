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

### 步骤1: 检测平台并提取字幕

根据视频URL识别平台，使用对应工具提取字幕：

**B站视频：**
```bash
# 列出可用字幕（需要Cookie）
yt-dlp --cookies <cookie文件> --list-subs "<视频URL>"

# 下载中文字幕（AI字幕优先）
yt-dlp --cookies <cookie文件> --write-subs --sub-lang ai-zh --convert-subs srt "<视频URL>" -o "subtitle"
```

**YouTube视频：**
```bash
# 列出字幕
yt-dlp --list-subs "<视频URL>"

# 下载字幕
yt-dlp --write-subs --sub-lang zh-CN --convert-subs srt "<视频URL>" -o "subtitle"
```

### 步骤2: 处理字幕文件

1. 读取SRT字幕文件
2. 提取纯文本（去除时间戳和序号）
3. 统计字幕时长和字数

### 步骤3: 生成内容总结

对提取的文本进行分析，生成结构化总结：
- 视频主题
- 核心内容/观点
- 关键要点（3-5条）
- 视频风格/来源

### 步骤4: 保存到飞书（可选）

如果用户要求保存到飞书：
1. 读取飞书配置（App ID, App Secret）
2. 调用飞书API创建记录
3. 包含：标题、URL、总结内容、关键词

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
| 无字幕可下载 | 提示用户登录或使用弹幕 |
| Cookie无效 | 提示用户重新提供Cookie |
| 网络超时 | 重试3次，每次间隔5秒 |
| 视频不存在 | 提示检查视频URL |

## 输出格式

### 字幕文件
- `subtitle.<lang>.srt` - SRT格式字幕
- `subtitle_text.txt` - 纯文本（去除时间戳）

### 内容总结
```markdown
## 视频内容总结

**平台**: B站/YouTube
**视频ID**: xxx
**时长**: xx:xx
**字幕行数**: xxx

### 主题

### 核心内容

### 关键要点
1. xxx
2. xxx
3. xxx
```

## 依赖

```bash
pip install yt-dlp
```

## 扩展计划

- [ ] 支持抖音/西瓜视频
- [ ] 支持本地视频语音识别
- [ ] 支持多语言字幕翻译
- [ ] 一键生成解读视频（调用content-video-generator）
