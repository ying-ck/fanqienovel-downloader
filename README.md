# Fanqienovel-downloader

## ⚠️ 重要公告
**由于API变更，v1.1.5及以下版本已失效，请立即升级至[v1.1.6+版本](https://github.com/ying-ck/fanqienovel-downloader/releases)**

---

## 📦 衍生工具
| 工具 | 描述 | 下载链接 |
|------|------|----------|
| c.exe | 检测网页结构变化 | [下载](https://github.com/ying-ck/fanqienovel-downloader/releases/tag/v1.1.13) |
| s.exe | 小说内容搜索工具 | [下载](https://github.com/qxqycb/search-novel) |
| f.exe | 文件分割工具 | [下载](https://github.com/qxqycb/novel-spilt) |

---

## 🖥️ 本地程序使用指南（v1.1.8+）

### 核心功能
1. **直接下载**  
   输入小说ID或完整目录页链接
2. **批量更新**  
   输入`1`读取record.json进行更新
3. **小说搜索**  
   输入`2`开启搜索功能
4. **批量下载**  
   输入`3`进行批量下载
5. **系统设置**  
   输入`4`配置：
   - 段首占位符
   - 请求延时（秒）
   - 存储路径
   - 保存模式
6. **数据备份**  
   输入`5`备份小说及配置
7. **退出程序**  
   输入`6`退出

### 📚 保存模式支持
1. 整本保存
2. 分章保存
3. EPUB电子书
4. HTML格式
5. LaTeX格式

---

## 💻 系统兼容性
| 操作系统 | 支持状态 |
|----------|----------|
| Windows 7-11 | ✔️ 正常 |
| macOS 10.1-10.9 | ✔️ 正常 |
| Kali Linux 2024.3 | ✔️ 正常 |

---

## 🌐 Web版功能
![Web界面预览](https://github.com/user-attachments/assets/2dfb008b-bdd7-4ff8-a020-cd1e5ede1dc9)

### 特色功能
- 远程下载直传本地
- 实时进度条显示
- ID/书名双模式下载
- 在线阅读支持
- 批量下载队列

### 部署方式
#### 1. 直接运行(windows)
下载[最新Release](https://github.com/ying-ck/fanqienovel-downloader/releases)的exe文件

#### 2. Python运行
```bash
git clone https://github.com/ying-ck/fanqienovel-downloader.git
cd fanqienovel-downloader
pip install -r requirements.txt
cd src
python server.py
# 访问 http://localhost:12930
```

#### 3. Docker部署
```bash
docker compose up -d
# 访问 http://localhost:12930
```

---

## 📱 手机端使用
### Termux配置
```bash
# 换源加速
sed -i 's@^(.*deb.*stable main)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main@' $PREFIX/etc/apt/sources.list
apt update && apt upgrade

# 安装依赖（需删除tkinter相关代码）
CFLAGS="-O0" pip install lxml requests ebooklib tqdm beautifulsoup4

# 运行程序
python ref_main.py
```
## 💻 linux_web部署
* （Ubuntu 24.10为例)使用python
### 安装系统依赖
```bash
sudo apt update
sudo apt install python3 python3-pip git
```

### 2. 克隆仓库
```bash
git clone https://github.com/ying-ck/fanqienovel-downloader.git
cd fanqienovel-downloader
cd src 
```
### 配置虚拟环境
```bash
python3 -m venv venv
```
### 激活虚拟环境
```bash
source myenv/bin/activate
```

### 安装Python环境
```bash
pip install -r requirements.txt
python server.py
```
### 退出虚拟环境
```bash
deactivate
```
#### 二次使用
```bash
# 进入fanqienovel-downloader-1.1.18/src/data
cd fanqienovel-downloader
cd src 
# 激活虚拟环境
source myenv/bin/activate
# 运行
python server.py
```


---

## ❓ 常见问题
**Q1：出现ProxyError怎么办？**  
A1：检查网络设置，关闭VPN/代理后重试

---

## ⚖️ 免责声明
> 本工具仅限技术研究用途，使用者需自行承担法律责任。开发者不对滥用行为负责。[完整协议](https://github.com/ying-ck/fanqienovel-downloader/blob/main/LICENSE)

---

## 🧑💻 开发团队
- **Yck** ([ying-ck](https://github.com/ying-ck))
- **Yqy** ([qxqycb](https://github.com/qxqycb))
- **Lingo** ([lingo34](https://github.com/lingo34))

## 📜 开源协议
[AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html)

---

![Stars](https://api.star-history.com/svg?repos=ying-ck/fanqienovel-downloader&type=Date)
![Alt](https://repobeats.axiom.co/api/embed/e76cbd049219133920a113b6f4f33973e36f7fd7.svg "Repobeats analytics image")
