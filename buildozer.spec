[app]

# 应用名称
title = Fanqie Novel Downloader

# 包名，确保唯一性
package.name = com.fanqie.novel_downloader

# 应用版本号
version = 1.0.0

# Python 版本
python_version = 3.8

# 所需的依赖项，这里假设只依赖 Kivy
requirements = kivy, requests, lxml, json, tqdm, beautifulsoup4

# Android 权限，如果需要访问网络
android.permissions = INTERNET

# 应用图标，假设图标文件为 icon.png，放在项目根目录下
icon.filename = icon.png