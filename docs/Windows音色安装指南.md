# Windows 下安装更多 pyttsx3 音色完整指南

> 本文档详细介绍在 Windows 系统上为 pyttsx3 安装更多语音包的所有方法，从简单的系统设置到高级的第三方引擎。

---

## 📋 目录

- [背景知识](#背景知识)
- [方案一：Windows 系统设置安装语言包（推荐）](#方案一windows-系统设置安装语言包推荐)
- [方案二：安装 RhVoice（免费开源）](#方案二安装-rhvoice免费开源)
- [方案三：使用 Balabolka 附带语音（免费）](#方案三使用-balabolka-附带语音免费)
- [方案四：安装 Microsoft Speech Platform](#方案四安装-microsoft-speech-platform)
- [方案五：第三方商业语音引擎](#方案五第三方商业语音引擎)
- [验证和测试](#验证和测试)
- [常见问题](#常见问题)

---

## 背景知识

pyttsx3 在 Windows 上使用 **SAPI5**（Speech API 5）作为语音后端。SAPI5 是微软提供的语音框架，所有已注册到系统的 SAPI5 兼容语音都可以被 pyttsx3 自动识别和使用。

**音色注册位置**：
```
HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens
```

每个语音在此路径下有一个独立的子项，包含语音的 ID、名称、语言等信息。

---

## 方案一：Windows 系统设置安装语言包（推荐）

> ⭐ **最简单、最推荐的方式**，适用于 Windows 10 / 11。

### 详细步骤

#### 1. 打开语言设置
- 按 `Win + I` 打开设置
- 进入 **时间和语言** → **语言和区域**

#### 2. 添加语言
- 点击 **"添加语言"** 按钮
- 在搜索框中输入目标语言名称，例如：
  - 日语、韩语、法语、德语、西班牙语、俄语、意大利语等

#### 3. 安装语言功能包
- 勾选语言后点击"下一步"
- **关键步骤**：确保勾选以下两项：
  - ✅ **语音识别**
  - ✅ **文本转语音**（或显示为"语音"）
- 点击"安装"

#### 4. 等待下载完成
- Windows 会从微软服务器下载语音包（通常几十 MB）
- 下载完成后无需重启电脑

#### 5. 验证安装
```bash
python list_voices.py
```
新安装的语音应该会出现在列表中。

### 常见语言包对应的语音名称

| 语言 | 语音名称示例 | 性别 |
|------|------------|------|
| 日语 (日本) | Microsoft Haruka Desktop - Japanese | 女声 |
| 日语 (日本) | Microsoft Ichiro Desktop - Japanese | 男声 |
| 韩语 (韩国) | Microsoft Heami Desktop - Korean | 女声 |
| 法语 (法国) | Microsoft Hortense Desktop - French | 女声 |
| 德语 (德国) | Microsoft Hedda Desktop - German | 女声 |
| 西班牙语 (墨西哥) | Microsoft Sabina Desktop - Spanish | 女声 |
| 俄语 (俄罗斯) | Microsoft Irina Desktop - Russian | 女声 |
| 意大利语 (意大利) | Microsoft Elsa Desktop - Italian | 女声 |

> 具体的语音名称取决于 Windows 版本和安装的语言包版本。

---

## 方案二：安装 RhVoice（免费开源）

### 特点

| 项目 | 说明 |
|------|------|
| 价格 | 完全免费 |
| 许可证 | 开源 (GPL) |
| 支持语言 | 俄语、英语、世界语、吉尔吉斯语、塔塔尔语等 |
| 兼容性 | SAPI5 兼容，pyttsx3 直接识别 |
| 音质 | ⭐⭐⭐ |

### 安装步骤

#### 1. 下载安装程序
- 访问官网：https://github.com/RhVoice/RhVoice/releases
- 下载 Windows 安装程序（`.exe` 或 `.msi`）

#### 2. 安装 RhVoice
- 运行安装程序
- 选择要安装的语言包
- 勾选 **SAPI5 集成**（确保 pyttsx3 能识别）
- 完成安装

#### 3. 验证
```bash
python list_voices.py
```

预期输出示例：
```
[2] RhVoice Russian (Alexander) 🇷🇺 俄文
    ID: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\RhVoice_Russian_Alexander
```

---

## 方案三：使用 Balabolka 附带语音（免费）

### 特点

| 项目 | 说明 |
|------|------|
| 价格 | 完全免费 |
| 包含语音 | 多个 SAPI5 兼容语音 |
| 兼容性 | 安装后自动注册到 SAPI5 |
| 附加功能 | 自带 TTS 文本转语音工具 |

### 安装步骤

#### 1. 下载 Balabolka
- 访问：http://www.cross-plus-a.com/balabolka.htm
- 下载 Windows 版本

#### 2. 安装
- 运行安装程序
- 安装过程中会附带多个语音引擎
- 语音会自动注册到 SAPI5

#### 3. 验证
```bash
python list_voices.py
```

---

## 方案四：安装 Microsoft Speech Platform

### 特点

| 项目 | 说明 |
|------|------|
| 价格 | 免费 |
| 支持语言 | 27 种语言 |
| 音质 | ⭐⭐⭐⭐（服务器级） |
| 兼容性 | ⚠️ 需要额外配置 |

### 安装步骤

#### 1. 下载 Speech Platform Runtime
- 访问：https://www.microsoft.com/en-us/download/details.aspx?id=27224
- 下载 `SpeechPlatformRuntime.msi` 并安装

#### 2. 下载语音包
- 访问：https://www.microsoft.com/en-us/download/details.aspx?id=27225
- 下载需要的语言语音包，例如：
  - `MSSpeech_TTS_zh-CN_HuiHui.msi`（中文女声）
  - `MSSpeech_TTS_en-US_Helen.msi`（英文女声）
  - `MSSpeech_TTS_ja-JP_Haruka.msi`（日文女声）

#### 3. 安装语音包
- 运行每个 `.msi` 文件完成安装

### ⚠️ 重要注意事项

> Microsoft Speech Platform 使用的注册表路径与 SAPI5 不同：
> ```
> HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech Server\v11.0\Voices\Tokens
> ```
> 而 pyttsx3 默认只读取：
> ```
> HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens
> ```
> 因此 **pyttsx3 默认不识别** Speech Platform 的语音。需要使用其他 TTS 库（如 `speechd`）或修改 pyttsx3 源码才能使用。

---

## 方案五：第三方商业语音引擎

### 推荐厂商

| 厂商 | 价格 | 支持语言 | 音质 | 网址 |
|------|------|---------|------|------|
| **CereProc** | 付费 | 26 种语言 | ⭐⭐⭐⭐ | https://www.cereproc.com |
| **Nuance** | 付费 | 35 种语言 | ⭐⭐⭐⭐ | https://www.nuance.com |
| **NeoSpeech** | 付费 | 中日韩英等 | ⭐⭐⭐⭐ | https://www.neospeech.com |

### 安装步骤

1. 访问厂商网站购买许可证
2. 下载安装程序
3. 安装后语音会自动注册到 SAPI5
4. 验证安装：
   ```bash
   python list_voices.py
   ```

---

## 验证和测试

### 快速验证

安装完语音后，运行项目自带的音色查看工具：

```bash
python list_voices.py
```

如果新语音出现在列表中，说明安装成功。

### 测试新语音

使用 curl 测试指定的音色：

```bash
# 测试第一个新安装的语音（假设索引是 2）
curl -X POST http://localhost:5001/api/speech ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"テスト\",\"voice\":\"2\"}"
```

### 在 Python 中直接试听

```python
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

# 列出所有语音
for i, v in enumerate(voices):
    print(f"{i}: {v.name}")

# 选择语音并试听
voice_index = 2  # 替换为你想测试的语音索引
engine.setProperty('voice', voices[voice_index].id)
engine.say('你好，这是一个测试')
engine.runAndWait()
```

---

## 常见问题

### Q1: 安装语音后 pyttsx3 没有识别到

**解决方法**：

1. **重启 Python** — pyttsx3 在初始化时读取注册表，需要重新启动
2. **检查注册表路径** — 确保语音注册在：
   ```
   HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens
   ```
3. **64 位系统检查** — 有些 32 位语音可能注册在：
   ```
   HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Microsoft\Speech\Voices\Tokens
   ```

### Q2: 为什么安装的语言包没有语音选项？

**原因**：部分语言包只包含界面翻译，不包含语音组件。

**解决方法**：
1. 在语言选项页面确认 **"文本转语音"** 是否已下载
2. 如果没有，点击"下载"按钮安装语音组件

### Q3: 如何删除不需要的语音？

**方法一** — 通过系统设置：
1. 设置 → 时间和语言 → 语言和区域
2. 点击不需要的语言 → 删除

**方法二** — 通过注册表（进阶）：
1. 按 `Win + R`，输入 `regedit`，打开注册表编辑器
2. 导航到 `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens`
3. 删除对应语音的注册表项

> ⚠️ **注意**：删除注册表项不会卸载语音引擎，只是让 pyttsx3 不再识别。

### Q4: 能不能在线安装更多语音？

**答案**：pyttsx3 本身是**离线库**，不支持在线语音。如果需要使用在线高质量语音，建议迁移到：

| 方案 | 特点 | 网址 |
|------|------|------|
| **edge-tts** | 微软 Edge 在线 TTS，免费 | https://github.com/rany2/edge-tts |
| **Azure TTS** | 微软 Azure 云语音，付费但质量极高 | https://azure.microsoft.com/services/cognitive-services/speech-services/ |
| **Google Cloud TTS** | Google 云语音 | https://cloud.google.com/text-to-speech |

### Q5: 系统默认只有一两个语音，正常吗？

**正常**。Windows 中文/英文版默认只安装中文和英文各一个语音。这是微软的默认配置，不是系统问题。

---

## 总结推荐

| 场景 | 推荐方案 |
|------|---------|
| **日常使用** | Windows 系统设置 → 添加语言包 |
| **免费多语言** | RhVoice（开源免费） |
| **追求音质** | 商业语音引擎（CereProc/NeoSpeech） |
| **企业级** | 迁移到 Azure TTS 或 edge-tts |
