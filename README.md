# Fanqienovel-downloader


### 由于开学的原因，作者无法及时回复，敬请谅解
### fanqienovel downloader v1.1.5及以下版本，由于API失效无法使用，现在请使用最新版本（v1.1.6及以上）：

下载番茄小说，通过Python实现
请勿滥用，且用且珍惜
## 使用方法

### v1.1.8版本及以上

1. 输入小说目录页面完整链接或者id下载
1. 输入id或链接直接下载
2. 输入1以更新，读取 record.json 中的id进行更新
3. 输入2进行搜索
4. 输入3进行批量下载
5. 输入4进入设置，可调整正文段首占位符，调整延时，小说存储位置，保存模式
6. 输入5进行备份下载的小说以及下载格式、段首空格等
7. 输入6退出程序

### v1.07版本及以上：
1. 输入小说目录页面完整链接或者id下载
1. 输入id或链接直接下载
2. 输入1以更新，读取 record.json 中的id进行更新
3. 输入2进行搜索
4. 输入3进行批量下载
5. 输入4进入设置，可调整正文段首占位符，调整延时，小说存储位置，保存模式
6. 输入5退出程序
### 目前(v1.1.3版本)保存方式支持：1.整本保存 2.分章保存 3.EPUB电子书格式保存 4.html格式保存 5.Latex格式保存

### 请注意！修改了设置中的每一个选项都会覆盖原来的数据，请仔细查看后在做出选择。若想修复默认选项，请将config.json文件删除

### 关于下载速度的问题
1.暂时不用多线程下载，因为怕被服务器封禁

### v1.07以下版本：
1. 输入id以下载，如：
**fanqienovel.com/page/7276384138653862966** 中的 **7276384138653862966**(可能会有另外两种：**fanqienovel.com/page/7276384138653862966?enter_from=stack-room**、**fanqienovel.com/page/7276384138653862966?enter_from=menu**，这样依旧选择数字：**7276384138653862966**)
2. 输入1以更新，读取 record.json 中的id进行更新
3. 输入2进入设置，可调整正文段首空格数，但空格数不为0时会花费额外时间进行处理；可选择下载小说保存方式(1.保存为单个txt；2.分章保存)；可选择小说保存路径；可选择章节下载间隔延迟(以避免对服务器造成过大压力，若延迟过小，可能导致你的IP地址被封)
4. 输入3退出程序

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
报错：The above exception was the direct cause of the following exception:
urllib3.exceptions.ProxyError: ('Unable to connect to proxy', FileNotFoundError(2, 'No such file or directory')) The above exception was the direct cause of the following exception:
Traceback (most recent call last):
File "requests\adapters. py", line 667, in send
File "urllib3\connectionpool. py", line 843, in urlopen File "urllib3\util\retry. py", line 519, in increment
urllib3. exceptions. MaxRetryError: HTTPSConnectionPool(host='fanqienovel. com', port=443): Max retries exceeded with url: /page/7143038691944959011 (Caused by ProxyError('Unable to connect to proxy', FileNotFoundError(2, 'No such file or dire ctory')))
......
### A1：
网络错误，请检查网络连接(如：关闭代理、加速)

## 注意

从旧版本(v1.00 ~ v1.05)升级到v1.0.6及更高版本需将json格式小说("(你下载的小说名).json")放入程序同文件夹下data/bookstore文件夹中，否则无法检测到原来的小说文件，将重新下载一次

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

- 作者：Yck (ying-ck) & Yqy(qxqycb)

## Star趋势

![Stars](https://api.star-history.com/svg?repos=ying-ck/fanqienovel-downloader&type=Date)
