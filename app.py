from flask import Flask, request, jsonify, render_template
import pyttsx3
import os
import time
from datetime import datetime

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'static/mp3'

# 确保mp3文件夹存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 初始化语音引擎
engine = pyttsx3.init()

@app.route('/api/speech', methods=['POST'])
def api_speech():
    data = request.get_json()
    text = data.get('text', '')
    voice_id = data.get('voice')

    # 生成唯一文件名
    timestamp = int(time.time())
    filename = f"api_{timestamp}.mp3"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 根据音色索引设置语音
    if voice_id is not None:
        voices = engine.getProperty('voices')
        try:
            voice_idx = int(voice_id)
            if 0 <= voice_idx < len(voices):
                engine.setProperty('voice', voices[voice_idx].id)
        except (ValueError, TypeError):
            pass  # 音色参数无效时使用默认语音

    # 保存语音文件
    engine.save_to_file(text, filepath)
    try:
        engine.runAndWait()
    except RuntimeError as e:
        if 'run loop already started' in str(e):
            engine.endLoop()
            engine.runAndWait()

    return jsonify({
        'status': 'success',
        'url': f"/static/mp3/{filename}"
    })

@app.route('/')
def index():
    # 获取所有可用的语音
    voices = engine.getProperty('voices')
    return render_template('index.html', voices=voices)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)