# Flask Text-to-Speech (Piper) 项目上下文

## 项目概述

基于 Flask + **Piper** 的离线神经网络文本转语音（TTS）Web 应用。
提供 Web 界面与 REST API，将文本合成为 WAV 音频并支持在线播放、下载与历史查看。

**版本**：v0.2.2（Piper 1.8.0，支持 `phoneme_type: pinyin` 中文音色；新增语音删除）

## 技术栈

- 后端：Python **3.11** + Flask 3.1.2
- TTS：piper-tts 1.8.0（`[zh]` extra：g2pW + transformers，用于拼音音素化）
- 前端：原生 HTML/CSS/JS（无构建步骤）
- 容器：Docker（amd64 + arm64 多架构）
- 音频：WAV / 22050 Hz / 16-bit 单声道

> piper-tts 1.8.0 使用 abi3 wheel，amd64/arm64 均有官方轮子；
> pinyin 音色依赖的 g2pW 模型与 BERT tokenizer 在构建时预置到 `/opt/piper-data`。

## 项目结构

```
flask-tts/
├── app.py                      # Flask 路由与 API
├── tts_engine.py               # Piper 引擎封装（发现/缓存/合成）
├── templates/index.html        # 单页界面（双栏：表单 + 预览/历史）
├── scripts/download_voices.py  # 语音模型下载（支持本地复用 + 断点续传）
├── scripts/download_g2pw.py    # 拼音音色资源（g2pW + BERT tokenizer）
├── assets/                     # 可选本地构建缓存（g2pw.tar.gz，不入库）
├── voices/                     # 预置模型目录（.gitkeep，模型不入库）
├── static/audio/               # 生成音频（卷挂载点）
├── Dockerfile
├── docker-compose.yml
└── docs/Piper迁移说明.md
```

## 关键模块

### `tts_engine.py`

- `VoiceInfo`：语音元信息（id/language/quality/phoneme_type/sample_rate/size...），`to_dict()` 不暴露服务器路径
- `PiperEngine`
  - `refresh()`：扫描 `PIPER_VOICE_DIRS`（默认 `/opt/piper-voices:/app/voices`），靠前目录优先
  - `voices` / `get(voice_id)`：排序规则为中文优先 → 语言 → 质量
  - `_load_model()`：延迟导入 `piper.PiperVoice`，`download_dir=PIPER_DATA_DIR`，加载后缓存在 `_models`
  - `synthesize(text, out_path, voice_id, speed)`：使用 `SynthesisConfig(length_scale=1/speed)`，逐句写入音频并插入 `PIPER_SENTENCE_SILENCE` 静音，`_synth_lock` 串行化合成

### `app.py`

| 路由 | 说明 |
|---|---|
| `GET /` | 渲染界面（按语言预分组传入 `voice_groups`） |
| `POST /api/speech` | 合成；`voice` 支持语音 ID 或数字索引（向后兼容） |
| `GET /api/voices` | 可用语音列表 |
| `GET /api/audio` | 已生成音频列表（读 `.json` 元数据，按时间倒序） |
| `DELETE /api/audio/<filename>` | 删除音频与元数据（校验文件名，支持前端历史列表删除） |
| `GET /health` | 健康检查（引擎、版本、语音数、phoneme_type） |

环境变量：`PORT`、`AUDIO_DIR`、`PIPER_VOICE_DIRS`、`PIPER_DATA_DIR`、`PIPER_SENTENCE_SILENCE`、`MAX_TEXT_LENGTH`、`FILE_MAX_AGE_HOURS`、`LOG_LEVEL`。

### `templates/index.html`

- 双栏布局：左栏输入（文本 / 音色 / 语速），右栏播放预览（上）+ 历史列表（下）
- Header 为紧凑单行品牌栏（图标 + 标题/副标题 + 离线徽标），节省垂直空间
- 音色下拉用 `<optgroup>` 按语言分组，`option value` 为**语音 ID**
- `setBtnLoading()` 每次重新查询 `#btnIcon` 再替换 `outerHTML`（避免引用失效导致转圈不消失）
- 历史列表用事件委托 + `data-index` 绑定，避免内联脚本注入问题
- 历史项提供下载与删除按钮；删除前 `confirm`，若删除当前预览项则重置播放器

## 数据与持久化

| 路径 | 内容 |
|---|---|
| `/opt/piper-voices` | 镜像内置模型（构建时下载，只读） |
| `/opt/piper-data` | g2pW 模型 + BERT tokenizer（构建时预置，只读） |
| `/app/voices` | 用户自定义语音（卷挂载） |
| `/app/static/audio` | 生成音频与元数据（卷挂载） |

## 构建与发布

```bash
# 本地单架构
docker build -t flask-tts .

# 多架构并推送
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ccr.ccs.tencentyun.com/mikewong/flask-tts:v0.2.2 \
  -t ccr.ccs.tencentyun.com/mikewong/flask-tts:latest \
  --provenance=false --push .
```

构建参数：`PIPER_VOICES`（内置语音列表）、`PIPER_VOICE_BASE`（模型源）、`PIPER_G2PW_URL` / `PIPER_BERT_BASE`（拼音资源源）、`PIP_INDEX_URL`（依赖源）。

若 `voices/` 目录已放模型文件、`assets/g2pw.tar.gz` 已放拼音资源，构建时直接复用、不联网。

## 注意事项

- 首次合成需加载 ONNX 模型（1–3 秒），之后走内存缓存
- 模型文件较大（medium ≈ 60 MB/语音），不要提交到 git
- 拼音音色（`phoneme_type=pinyin`）额外需要 159 MB 的 g2pW ONNX 模型；不要删除 `/opt/piper-data`
- 构建镜像时模型下载容易受网络影响：优先用 `scripts/download_voices.py --out ./voices` 预下载
- g2pw.tar.gz 约 108 MB，HuggingFace Xet 长连接易断；下载脚本按 8 MB 分块重试
- piper 语音索引中的 `size_bytes` 可能与镜像站文件略有差异（版本漂移），下载脚本不再依赖索引大小校验
- QEMU 模拟 arm64 合成极慢（约 180 秒/句），属正常现象；真机 arm64 约 1 秒
