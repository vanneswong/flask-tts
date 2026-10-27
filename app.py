from flask import Flask, request, jsonify, render_template
import pyttsx3
import os
import time
import uuid
import threading
import logging
import json
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/audio'

# 确保audio文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 初始化语音引擎
engine = pyttsx3.init()

# 线程锁（保护 pyttsx3 引擎的并发访问）
engine_lock = threading.Lock()

# 最大文本长度限制
MAX_TEXT_LENGTH = 5000

# 文件保留时长（小时）
FILE_MAX_AGE_HOURS = 24

# 应用版本号
APP_VERSION = '0.1.0'


def cleanup_old_files(max_age_hours=24):
    """清理超过指定小时的旧文件"""
    folder = Path(app.config['UPLOAD_FOLDER'])
    if not folder.exists():
        return

    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    cleaned = 0

    for file in folder.glob('*.wav'):
        if file.stat().st_mtime < cutoff:
            file.unlink()
            # 同时清理对应的元数据文件
            meta = file.with_suffix('.json')
            if meta.exists():
                meta.unlink()
            cleaned += 1

    if cleaned > 0:
        logger.info(f"已清理 {cleaned} 个过期语音文件")


# 应用启动时清理旧文件
cleanup_old_files(max_age_hours=FILE_MAX_AGE_HOURS)

@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'error': '请求体不能为空'}), 400

    text = data.get('text', '').strip()
    if not text:
        return jsonify({'status': 'error', 'error': '文本内容不能为空'}), 400

    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({
            'status': 'error',
            'error': f'文本长度不能超过 {MAX_TEXT_LENGTH} 字符'
        }), 400

    voice_id = data.get('voice')

    logger.info(f'Speech request: text_length={len(text)}, voice={voice_id}, '
                f'ip={request.remote_addr}')

    # 使用 UUID 生成唯一文件名，避免并发冲突
    filename = f"api_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 使用线程锁保护引擎调用
    voice_name = '默认语音'
    with engine_lock:
        # 根据音色索引设置语音（与前端一致：使用过滤后的中英文音色列表）
        if voice_id is not None:
            voices = _filter_voices(engine.getProperty('voices'))
            try:
                voice_idx = int(voice_id)
                if 0 <= voice_idx < len(voices):
                    engine.setProperty('voice', voices[voice_idx].id)
                    voice_name = voices[voice_idx].name
            except (ValueError, TypeError):
                pass  # 音色参数无效时使用默认语音

        # 保存语音文件
        engine.save_to_file(text, filepath)
        try:
            engine.runAndWait()
        except RuntimeError as e:
            if 'run loop already started' in str(e):
                try:
                    engine.endLoop()
                    engine.runAndWait()
                except Exception:
                    logger.error('Speech generation failed: run loop error')
                    return jsonify({
                        'status': 'error',
                        'error': '语音生成失败'
                    }), 500
            else:
                logger.error(f'Speech generation failed: {e}')
                return jsonify({
                    'status': 'error',
                    'error': '语音生成失败'
                }), 500
        except Exception as e:
            logger.error(f'Speech generation failed: {e}')
            return jsonify({
                'status': 'error',
                'error': '语音生成失败'
            }), 500

    # 保存元数据（用于历史列表展示）
    meta_path = os.path.splitext(filepath)[0] + '.json'
    try:
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({
                'text': text,
                'voice': voice_name,
                'created_at': time.time()
            }, f, ensure_ascii=False)
    except Exception as e:
        logger.warning(f'Failed to save metadata: {e}')

    logger.info(f'Speech generated successfully: {filename}')
    return jsonify({
        'status': 'success',
        'url': f"/static/audio/{filename}"
    })

def _filter_voices(voices):
    """过滤语音，只保留中文和英文"""
    zh_keywords = ['zh', 'cmn', 'yue', 'hak', 'chinese', 'mandarin', 'cantonese']
    en_keywords = ['en', 'english']

    def is_zh_or_en(voice_id):
        vid = voice_id.lower()
        for kw in zh_keywords:
            if kw in vid:
                return True
        for kw in en_keywords:
            if kw in vid:
                return True
        return False

    return [v for v in voices if is_zh_or_en(v.id)]


@app.route('/health')
def health():
    """健康检查接口"""
    voices = engine.getProperty('voices')
    filtered = _filter_voices(voices)
    return jsonify({
        'status': 'healthy',
        'uptime': 'running',
        'available_voices': len(filtered),
        'total_voices': len(voices)
    })


@app.route('/api/audio')
def api_audio_list():
    """返回已生成的语音文件列表（用于前端历史列表）"""
    folder = Path(app.config['UPLOAD_FOLDER'])
    items = []
    if folder.exists():
        for f in folder.glob('*.wav'):
            meta = {}
            meta_file = f.with_suffix('.json')
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding='utf-8'))
                except Exception:
                    meta = {}
            try:
                stat = f.stat()
                items.append({
                    'filename': f.name,
                    'url': f"/static/audio/{f.name}",
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'text': meta.get('text', ''),
                    'voice': meta.get('voice', ''),
                    'created_at': meta.get('created_at', stat.st_mtime)
                })
            except OSError:
                continue

    # 按创建时间倒序排列（最新的在前）
    items.sort(key=lambda x: x.get('created_at', 0), reverse=True)
    return jsonify({'status': 'success', 'items': items})


@app.route('/')
def index():
    """主页"""
    all_voices = engine.getProperty('voices')
    voices = _filter_voices(all_voices)
    return render_template('index.html', voices=voices, version=APP_VERSION)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask Text-to-Speech Application')
    parser.add_argument('port', type=int, nargs='?', default=5001,
                        help='Port to run the server on (default: 5001)')
    args = parser.parse_args()
    
    logger.info(f"Starting Flask Text-to-Speech application on port {args.port}")
    app.run(host='0.0.0.0', port=args.port)