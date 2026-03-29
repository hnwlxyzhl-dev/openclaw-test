# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 📊 PPT工具快速参考

### 工具清单

#### 1. python-pptx（本地方案）
- **类型：** Python库
- **安装：** `pip install python-pptx`
- **费用：** 免费
- **完成度：** 93%
- **限制：** 不支持动画
- **最佳脚本：** `generate_ppt_v5_ultimate.py`
- **文档：** `PPT工具完整知识库.md`

#### 2. 2slides MCP（云端方案）⭐ 推荐
- **类型：** MCP服务器
- **官网：** https://2slides.com
- **GitHub：** https://github.com/2slides/mcp-2slides
- **API：** https://2slides.com/api
- **费用：** 付费（1-210积分/页）
- **功能：** Fast PPT, Nano Banana, AI配音
- **配置路径：** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **支持中文：** ✅

### 快速决策

**需要快速PPT（预算充足）：**
→ 使用2slides Fast PPT（1积分/页，5分钟）

**需要专业PPT（预算充足）：**
→ 使用2slides Nano Banana（100积分/页，10分钟）

**需要AI配音PPT：**
→ 使用2slides + AI配音（210积分/页）

**预算有限：**
→ 使用python-pptx（93%完成度，已完成）

**需要100%完美：**
→ python-pptx + 手动动画（免费，15分钟）

### 2slides MCP配置模板

```json
{
  "mcpServers": {
    "2slides": {
      "command": "npx",
      "args": ["2slides-mcp"],
      "env": {
        "API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

### 2slides常用功能

**搜索主题：**
```javascript
themes_search(query="business", limit=10)
```

**快速生成：**
```javascript
slides_generate(
  themeId="st-xxx",
  userInput="生成5页ML介绍",
  responseLanguage="Simplified Chinese",
  mode="sync"
)
```

**专业生成：**
```javascript
slides_create_pdf_slides(
  userInput="内容",
  designStyle="现代、深色",
  aspectRatio="16:9",
  resolution="2K",
  mode="async"
)
```

**添加配音：**
```javascript
slides_generate_narration(
  jobId="xxx",
  mode="multi",
  speaker1Name="张三",
  speaker1Voice="Aoede"
)
```

### 已创建的PPT文件

- `如何制作专业级PPT_v5_ultimate.pptx` ⭐ 推荐（93%完成度）
- 18页完整内容
- 专业蓝色主题
- 包含图表和配色展示

### 详细文档位置

- 完整知识库：`PPT工具完整知识库.md` (9,104字)
- 2slides学习笔记：`2slides-MCP完整学习笔记.md` (4,695字)
- 动画技术研究：`PPT动画技术研究完整报告.md` (3,433字)
- 生成脚本：`generate_ppt_v5_ultimate.py` (23KB)

### 重要经验

1. ✅ **主动搜索工具** - 不要等用户提示
2. ✅ **检查MCP生态** - https://github.com/modelcontextprotocol/servers
3. ✅ **追求完美** - 不满足于"够用"
4. ✅ **提供选择** - 列出所有方案，让用户决定

---

Add whatever helps you do your job. This is your cheat sheet.
