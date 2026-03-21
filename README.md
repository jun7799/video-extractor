# video-extractor

视频字幕提取与内容解读工具

## 功能

- 支持 B站 / YouTube 视频字幕自动提取
- 自动生成内容总结
- 支持保存到飞书多维表格

## 安装

```bash
pip install yt-dlp
```

## 使用方法

### 1. 配置 B站 Cookie（可选）

如需提取 B站视频的 AI 字幕，需要配置 Cookie：

1. 登录 B站
2. 按 `F12` → Application → Cookies → `www.bilibili.com`
3. 导出以下 Cookie 值：
   - SESSDATA
   - bili_jct
   - DedeUserID
   - DedeUserID__ckMd5

4. 创建 `bilibili_cookies.txt` 文件，格式如下：

```
# Netscape HTTP Cookie File
.bilibili.com	TRUE	/	TRUE	<过期时间戳>	SESSDATA	<你的SESSDATA值>
.bilibili.com	TRUE	/	TRUE	<过期时间戳>	bili_jct	<你的bili_jct值>
.bilibili.com	TRUE	/	TRUE	<过期时间戳>	DedeUserID	<你的DedeUserID值>
.bilibili.com	TRUE	/	TRUE	<过期时间戳>	DedeUserID__ckMd5	<你的DedeUserID__ckMd5值>
```

### 2. 提取字幕

**B站视频：**
```bash
yt-dlp --cookies bilibili_cookies.txt --write-subs --sub-lang ai-zh --convert-subs srt "https://www.bilibili.com/video/BVxxxxx"
```

**YouTube视频：**
```bash
yt-dlp --write-subs --sub-lang zh-CN --convert-subs srt "https://www.youtube.com/watch?v=xxxxx"
```

### 3. 提取纯文本

```bash
python scripts/extract_text.py subtitle.srt -o output.txt
```

## 触发关键词

当你说以下内容时会自动触发此技能：
- "提取视频字幕"
- "解读B站视频"
- "分析YouTube视频"
- "把视频做成文字总结"

## 项目结构

```
video-extractor/
├── SKILL.md              # 技能定义文件
├── README.md             # 使用说明
├── .gitignore            # 忽略敏感文件
├── evals/
│   └── evals.json        # 测试用例
└── scripts/
    └── extract_text.py   # 字幕提取脚本
```

## 依赖

- Python 3.8+
- yt-dlp

## License

MIT
