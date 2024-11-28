#### 现在有一种方式可在手机上使用(只是ref_main.py,不是web版)

安装termux

换源：
1.sed -i 's@^ $deb.*stable main$ $@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/apt/termux-main stable main@' $PREFIX/etc/apt/sources.list
2.apt update && apt upgrade

3.pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

安装包：
pip install requests lxml ebooklib tqdm beautifulsoup4(注意：在ref_main.py中删掉tkinter的导入)

运行：
python ref_main.py

注意：运行环境配置正确，不要对应错误
安装lxml库可能报错，按照以下步骤解决：
apt install clang 
apt install libxml2
apt install libxslt 
pip install cython 
pip install lxml 

