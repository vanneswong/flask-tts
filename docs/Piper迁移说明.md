# Piper 迁移说明（v0.1.0 → v0.2.0）

## 背景

v0.1.0 使用 pyttsx3 + espeak-ng 合成语音，中文音质机械、断句生硬，且存在两个实现缺陷：

1. 实际输出 WAV 却命名为 `.mp3`，浏览器按 MP3 解码 → 噪音
2. 前端下拉框用「过滤后」语音列表，后端用「完整」列表取索引 → 音色错配

v0.2.0 直接更换引擎为 Piper（VITS 神经网络 TTS），上述问题从根上消失。

---

## 变更清单

| 文件 | 变更 |
|---|---|
| `tts_engine.py` | **新增**：Piper 引擎封装（语音发现、模型缓存、合成） |
| `app.py` | 重写：移除 pyttsx3，接入 `PiperEngine`，新增 `/api/voices` |
| `templates/index.html` | 音色改用语音 ID + 按语言分组；新增语速滑杆；保留双栏与历史列表 |
| `requirements.txt` | `pyttsx3` → `piper-tts==1.2.0` |
| `Dockerfile` | Python 3.12 → **3.11**；去 espeak-ng；构建期下载/复用语音模型；新增 `/app/voices` 卷 |
| `scripts/download_voices.py` | **新增**：按 piper 内置索引下载模型，支持本地复用与断点续传 |
| `docker-compose.yml` | **新增** |
| `.dockerignore` | **新增** |
| `README.md` / `AGENT.md` | 按 Piper 重写 |
| `deploy/ubuntu/` | **移除**：该系统 systemd 部署包基于 pyttsx3 + espeak-ng，已不适用（保留在 `pyttsx3` 分支） |
| `list_voices.py` / `fix_voices.py` | **移除**：pyttsx3 专用工具（语音列表改由 `GET /api/voices` 提供） |

---

## 接口兼容性

`POST /api/speech` 保持兼容：

- `voice` 现在推荐传**语音 ID**（如 `zh_CN-huayan-medium`）
- 仍兼容旧的**数字索引**（如 `"0"`），会映射到语音列表对应项

新增可选字段 `speed`（0.5–2.0，默认 1.0）。

新增接口 `GET /api/voices`。

`/health` 响应新增 `engine`、`version`、`voices` 字段。

---

## 为什么用 Python 3.11

v0.2.0 使用 `piper-tts 1.2.0`（依赖 `piper-phonemize 1.1.0`，其 aarch64 wheel
只覆盖 cp39–cp311），因此当时选定 3.11。

v0.2.2 升级到 `piper-tts 1.8.0` 后，该包使用 abi3 wheel（cp39+，amd64/arm64 均有），
Python 3.11 已不再是硬性限制；镜像继续使用 3.11 以保持一致性与稳定性。

## v0.2.2：升级到 piper-tts 1.8.0

v0.2.1 使用 `piper-tts 1.2.0`，其 `PhonemeType` 只有 `espeak`，遇到
`"phoneme_type": "pinyin"` 的中文音色（如 `zh_CN-chaowen-medium`、
`zh_CN-xiao_ya-medium`）会直接报错：

```
'pinyin' is not a valid PhonemeType
```

v0.2.2 升级到 `piper-tts 1.8.0` 并安装 `[zh]` extra：

| 变化 | 说明 |
|---|---|
| `requirements.txt` | `piper-tts[zh]==1.8.0` |
| 拼音资源 | 构建时预置 g2pW 模型（159 MB）与 `bert-base-chinese` tokenizer 到 `/opt/piper-data` |
| 合成 API | 改为 `PiperVoice.synthesize()` + `SynthesisConfig(length_scale=...)`，逐句写入并插入静音 |
| 离线运行 | `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1`，g2pW `config.py` 指向本地 tokenizer |
| 默认音色 | 增加 `zh_CN-chaowen-medium`、`zh_CN-xiao_ya-medium` |
| 前端 | Header 改为紧凑单行；历史列表新增删除按钮 |
| API | 新增 `DELETE /api/audio/<filename>` |

> 与旧文档中的结论不同：1.8.0 的 `[zh]` extra 自 1.6.1 起已移除 torch 依赖，
> 仅使用 onnxruntime + transformers 的 tokenizer，镜像体积增量主要来自 g2pW 模型。

---

## 实测数据

| 项目 | 值 |
|---|---|
| 中文模型 | `zh_CN-huayan-medium`（63.2 MB, 22050 Hz） |
| 英文模型 | `en_US-lessac-medium`（63.2 MB, 22050 Hz） |
| 首次合成 | 约 3.3 s（含模型加载） |
| 后续合成 | 约 0.5–0.8 s（一句中文） |
| 音频校验 | 时长与文本长度相符，RMS ≈ 6000（非静音/非削波） |

---

## 回退方式

```bash
git checkout pyttsx3          # 源码回退
# 或使用旧镜像
docker run -p 5001:5001 ccr.ccs.tencentyun.com/mikewong/flask-tts:v0.1.0
```

---

## 后续可做

- 换用 `uvicorn + gunicorn` 生产服务器（当前为 Flask 开发服务器）
- 按句子流式返回音频，降低长文本首字延迟
- 支持多说话人模型的 `speaker_id` 选择
- 为 `/api/speech` 增加限流与鉴权
