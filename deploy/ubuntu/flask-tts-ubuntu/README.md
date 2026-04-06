# Flask 文本转语音应用 - Ubuntu 部署包

> 适用于 Ubuntu 18.04+ / Debian 10+ 系统

---

## 📁 部署包内容

```
flask-tts-ubuntu/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── list_voices.py         # 音色查看工具
├── deploy.sh              # 一键部署脚本
├── README.md              # 本文件
├── templates/
│   └── index.html         # Web 界面
└── static/
    └── mp3/               # 语音文件存储目录
```

---

## 🚀 快速部署

### 1. 上传到服务器

```bash
# 方式一：使用 scp 上传
scp flask-tts-ubuntu.tar.gz user@server:/path/to/

# 方式二：使用 sftp 上传
sftp user@server
put flask-tts-ubuntu.tar.gz
```

### 2. 解压并部署

```bash
# 解压
tar -xzf flask-tts-ubuntu.tar.gz
cd flask-tts-ubuntu

# 运行部署脚本
bash deploy.sh
```

部署脚本会自动完成：
- ✅ 检查系统环境（Python、espeak）
- ✅ **交互式选择端口**（1024-65535）
- ✅ 创建 Python 虚拟环境
- ✅ 安装所有依赖
- ✅ 配置 systemd 服务
- ✅ 启动服务

### 3. 访问应用

部署完成后，根据提示的端口访问：
- Web 界面：`http://你的服务器IP:端口`
- API 接口：`http://你的服务器IP:端口/api/speech`
- 健康检查：`http://你的服务器IP:端口/health`

---

## 📖 手动部署

如果不想使用自动部署脚本，可以按以下步骤手动部署。

### 1. 安装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv espeak libespeak-dev
```

### 2. 创建虚拟环境

```bash
cd flask-tts-ubuntu
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 启动应用

```bash
# 指定端口启动（例如 8080）
python app.py 8080
```

### 4. 配置 systemd 服务（可选）

创建服务文件：

```bash
sudo nano /etc/systemd/system/flask-tts.service
```

写入以下内容（替换 `<用户>`、`<项目路径>`、`<端口>`）：

```ini
[Unit]
Description=Flask Text-to-Speech Application
After=network.target

[Service]
Type=simple
User=<用户>
Group=<用户>
WorkingDirectory=<项目路径>
Environment="PATH=<项目路径>/venv/bin"
ExecStart=<项目路径>/venv/bin/python app.py <端口>
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable flask-tts
sudo systemctl start flask-tts
```

---

## 🔧 服务管理

### 常用命令

```bash
# 查看服务状态
sudo systemctl status flask-tts

# 停止服务
sudo systemctl stop flask-tts

# 启动服务
sudo systemctl start flask-tts

# 重启服务
sudo systemctl restart flask-tts

# 查看实时日志
journalctl -u flask-tts -f

# 查看最近 100 行日志
journalctl -u flask-tts -n 100
```

### 修改端口

1. 编辑服务文件：
   ```bash
   sudo nano /etc/systemd/system/flask-tts.service
   ```

2. 修改 `ExecStart` 行末尾的端口号：
   ```ini
   ExecStart=/path/to/venv/bin/python app.py 新端口
   ```

3. 重载并重启：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart flask-tts
   ```

---

## 🌐 Nginx 反向代理（可选）

如果你想通过 80/443 端口访问应用，可以配置 Nginx 反向代理。

### 1. 安装 Nginx

```bash
sudo apt install -y nginx
```

### 2. 创建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/flask-tts
```

写入以下内容（替换 `<端口>` 为实际端口）：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:<端口>;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/flask-tts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. 配置 HTTPS（可选）

使用 Let's Encrypt 免费证书：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

---

## 🔍 查看可用音色

```bash
source venv/bin/activate
python list_voices.py
```

---

## ❓ 常见问题

### Q1: 服务启动失败

**查看日志**：
```bash
journalctl -u flask-tts -e
```

常见原因：
- 端口被占用：更换端口
- espeak 未安装：`sudo apt install espeak libespeak-dev`
- 依赖未安装：`source venv/bin/activate && pip install -r requirements.txt`

### Q2: 中文语音乱码

确保系统安装了中文字体：
```bash
sudo apt install -y fonts-wqy-zenhei fonts-wqy-microhei
```

### Q3: 防火墙阻止访问

如果使用 UFW 防火墙，放行端口：
```bash
sudo ufw allow <端口>/tcp
```

### Q4: 如何更新应用代码

1. 停止服务：
   ```bash
   sudo systemctl stop flask-tts
   ```

2. 替换 `app.py` 和 `templates/index.html`

3. 重启服务：
   ```bash
   sudo systemctl start flask-tts
   ```

---

## 🗑 卸载

```bash
# 停止服务
sudo systemctl stop flask-tts
sudo systemctl disable flask-tts

# 删除服务文件
sudo rm /etc/systemd/system/flask-tts.service
sudo systemctl daemon-reload

# 删除项目目录
rm -rf flask-tts-ubuntu
```
