# Ubuntu 部署指南

> 适用于 Ubuntu 18.04+ / Debian 10+ 系统

---

## 📋 目录

- [部署方式选择](#部署方式选择)
- [方式一：使用自包含部署包（推荐）](#方式一使用自包含部署包推荐)
- [方式二：使用 Git 克隆](#方式二使用-git-克隆)
- [服务管理](#服务管理)
- [Nginx 反向代理（可选）](#nginx-反向代理可选)
- [常见问题](#常见问题)

---

## 部署方式选择

本项目提供两种部署方式，请根据需求选择：

| 方式 | 适用场景 | 优点 |
|------|---------|------|
| **自包含部署包** | 生产环境、快速部署 | 文件精简、无需 Git、即传即用 |
| **Git 克隆** | 开发环境、需要更新代码 | 方便拉取更新、包含完整项目 |

---

## 方式一：使用自包含部署包（推荐）

### 1. 打包部署包

在项目根目录运行：

```bash
bash deploy/ubuntu/package.sh
```

打包完成后，会生成 `deploy/ubuntu/flask-tts-ubuntu.tar.gz`。

### 2. 上传到服务器

```bash
# 方式一：使用 scp
scp deploy/ubuntu/flask-tts-ubuntu.tar.gz user@服务器IP:/home/user/

# 方式二：使用 sftp
sftp user@服务器IP
put deploy/ubuntu/flask-tts-ubuntu.tar.gz
```

### 3. 解压并部署

```bash
# SSH 登录服务器
ssh user@服务器IP

# 解压
tar -xzf flask-tts-ubuntu.tar.gz
cd flask-tts-ubuntu

# 运行部署脚本
bash deploy.sh
```

### 部署脚本会自动完成

| 步骤 | 说明 |
|------|------|
| 1/5 | 检查系统环境（Python、espeak） |
| 2/5 | **交互式选择端口**（1024-65535） |
| 3/5 | 创建 Python 虚拟环境 |
| 4/5 | 安装所有依赖 |
| 5/5 | 配置 systemd 服务并启动 |

### 部署包内容

```
flask-tts-ubuntu/
├── app.py                 # Flask 主应用
├── requirements.txt       # Python 依赖
├── list_voices.py         # 音色查看工具
├── deploy.sh              # 一键部署脚本
├── README.md              # 部署说明
├── templates/
│   └── index.html         # Web 界面
└── static/
    └── mp3/               # 语音文件存储目录
```

---

## 方式二：使用 Git 克隆

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd flask-text2speech-pyttsx3
```

### 2. 运行部署脚本

```bash
bash deploy/ubuntu/deploy.sh
```

脚本会自动完成环境检查、虚拟环境创建、依赖安装和服务配置。

---

## 服务管理

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

### 查看可用音色

```bash
source venv/bin/activate
python list_voices.py
```

---

## Nginx 反向代理（可选）

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

## 常见问题

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

### Q4: 部署脚本报错"权限不足"

**解决**：使用 `bash` 命令运行：
```bash
bash deploy.sh
```

### Q5: 如何更新应用代码

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

## 卸载

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
