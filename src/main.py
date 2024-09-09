import init
from function import update,search,multiDownload,setting,download


def loop() -> None:
    print('\n输入书的id直接下载\n输入下面的数字进入其他功能:')
    print('''
1. 更新小说
2. 搜索
3. 批量下载
4. 设置
5. 重载配置文件
6. 退出
''')

    inp = input()

    match inp:
        case '1':
            update()
        case '2':
            search()
        case '3':
            multiDownload()
        case '4':
            setting()
        case '5':
            init.init_config()
        case '6':
            quit(0)
        case _ if inp:
            download(inp)


def main() -> None:
    init.init_config()
    while True:
        loop()

if __name__ == "__main__":
    main()