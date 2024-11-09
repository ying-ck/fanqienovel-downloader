# Fanqienovel-downloader


### 由于上学的原因，作者无法及时回复，敬请谅解
### fanqienovel downloader v1.1.5及以下版本，由于API失效无法使用，现在请使用最新版本（v1.1.6及以上）：

下载番茄小说，通过Python实现
请勿滥用，且用且珍惜

## 衍生工具
1.[c.exe](https://github.com/ying-ck/fanqienovel-downloader/releases/tag/v1.1.13)用于检测番茄小说网页结构变化

2.[s.exe](https://github.com/qxqycb/search-novel)用于小说内容搜索，可搭配番茄小说下载器使用

3.[f.exe](https://github.com/qxqycb/novel-spilt)以文件大小来分割小说文件，可搭配番茄小说下载器使用

## 使用方法

### 本地程序

### v1.1.8版本及以上

1. 输入小说目录页面完整链接或者id下载
1. 输入id或链接直接下载
2. 输入1以更新，读取 `record.json` 中的id进行更新
3. 输入2进行搜索
4. 输入3进行批量下载
5. 输入4进入设置，可调整正文段首占位符，调整延时，小说存储位置，保存模式
6. 输入5进行备份下载的小说以及下载格式、段首空格等
7. 输入6退出程序


### 目前(v1.1.14版本)保存方式支持：1.整本保存 2.分章保存 3.EPUB电子书格式保存 4.html格式保存 5.Latex格式保存

### 请注意！修改了设置中的每一个选项都会覆盖原来的数据，请仔细查看后在做出选择。若想修复默认选项，请将`config.json`文件删除

## fanqienovel downloader 在各个系统上的运行情况:
| 系统(System) | 运行情况(Operation) |
| ---------------- | ------------------------ |
| windows 7 |可运行 |
| windows 10 |可运行 |
| windows 11|可运行 |
| mac OS X 10.1 | 可运行 |
| mac OS X 10.2 | 可运行 |
| mac OS X 10.3 | 可运行 |
| mac OS X 10.4 | 可运行 |
| mac OS X 10.5 | 可运行 |
| mac OS X 10.6 | 可运行 |
| mac OS X 10.7 | 可运行 |
| mac OS X 10.8 | 可运行 |
| mac OS X 10.9 | 可运行 |
| Kali Linux 2024.3 | 可运行 |

## Q&A
### Q1：
报错：` The above exception was the direct cause of the following exception:
urllib3.exceptions.ProxyError: ('Unable to connect to proxy', FileNotFoundError(2, 'No such file or directory')) The above exception was the direct cause of the following exception:
Traceback (most recent call last):
File "requests\adapters. py", line 667, in send
File "urllib3\connectionpool. py", line 843, in urlopen File "urllib3\util\retry. py", line 519, in increment
urllib3. exceptions. MaxRetryError: HTTPSConnectionPool(host='fanqienovel. com', port=443): Max retries exceeded with url: /page/7143038691944959011 (Caused by ProxyError('Unable to connect to proxy', FileNotFoundError(2, 'No such file or dire ctory'))) `
......
### A1：
网络错误，请检查网络连接(如：关闭代理、加速)

### Web 版

<img src="https://github.com/user-attachments/assets/b81aa6d7-3349-4167-ad62-cb6caffb3cf0" width="500">
<img src="https://github.com/user-attachments/assets/b8f469ed-98dd-4ea6-9a90-901c7644f9a8" width="500">
<img src="https://github.com/user-attachments/assets/4e667d93-646f-4b1e-bcec-a869520845b3" width="500">


Web版实现的功能
- 网页服务器下载完直接让你下载小说文件到本地，所以能远程放在容器或虚拟机中运行。
- 有进度条，漂亮！
- 能透过 id 下载小说，也能用名字搜索小说，更能更新之前下载的小说。
- 简洁的 UI 界面。
- 队列设计，可以把好几本书加入队列，批量下载。
- (而且把原本的代码重构了一下，至于变好还是变坏我不好说，主要是之前的代码搞成web 不太方便)
- 在线阅读

你有3种方式运行 web 版。

1.直接执行exe文件

2. Python 运行

用 Git 克隆这个项目或直接下载项目的zip并解压。进入项目文件夹，新建虚拟环境，并用 `pip install -r requirements.txt` 来安装这个项目的 python 依赖。

接着进入`src`目录，用python 运行 `server.py`，并根据指示用浏览器开启 `http://localhost:12930`。
(注意：`python`版本3.8及以下版本下载项目`zip`或`git`时，`src`目录中,将原来的`main.py`删除，再把`main2.py`名称改为`main.py`)

3. Docker 运行

用 Git 克隆这个项目或直接下载项目的zip并解压。进入项目文件夹。

直接使用 `docker compose up` (或是 `docker compose up -d` 在后台运行) 构建并启动镜像。启动后用浏览器访问 `http://localhost:12930`。

下载的小说和个人数据 (`data` 文件夹) 会存在docker 卷里面，分别叫做 `fanqie_data` 和 `fanqie_downloads`。如果你想修改成某个特定的目录，可以修改 `docker-compose.yaml` 文件中的持久化用户数据部分。

## 集思广益

若各位使用者有什么意见或程序有什么错误，欢迎在lssues中讨论

## 免责声明

此程序旨在用于与Python网络爬虫和网页处理技术相关的教育和研究目的。不应将其用于任何非法活动或侵犯他人权利的行为。用户对使用此程序引发的任何法律责任和风险负有责任，作者和项目贡献者不对因使用程序而导致的任何损失或损害承担责任

在使用此程序之前，请确保遵守相关法律法规以及网站的使用政策，并在有任何疑问或担忧时咨询法律顾问

This program is designed for educational and research purposes related to Python web crawlers and web page processing technologies. It should not be used for any illegal activities or acts that violate the rights of others. Users are responsible for any legal liabilities and risks arising from the use of this program. The author and project contributors are not responsible for any losses or damages resulting from the use of the program.

Before using this program, please ensure compliance with relevant laws and regulations and the website's usage policies. Consult a legal advisor if you have any questions or concerns.

## 开源

本程序遵循[AGPL-3.0](https://github.com/ying-ck/fanqienovel-downloader?tab=AGPL-3.0-1-ov-file)开源。使用本程序源码时请注明来源，并同样使用此协议。

## 作者

- 作者：Yck (ying-ck) & Yqy(qxqycb) & Lingo(lingo34)

## Star趋势

![Stars](https://api.star-history.com/svg?repos=ying-ck/fanqienovel-downloader&type=Date)
