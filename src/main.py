from tmp import Config, NovelDownloader
from functions import check_backup, update_all, search, batch_download, settings, backup, download_novel

def loop(downloader: NovelDownloader, config: Config):
    print('\n输入书的id直接下载\n输入下面的数字进入其他功能:')
    print('''
1. 更新小说
2. 搜索
3. 批量下载
4. 设置
5. 备份
6. 退出
        ''')

    inp = input()
    if inp == '1':
        update_all(downloader)
    elif inp == '2':
        search(downloader)
    elif inp == '3':
        batch_download(downloader)
    elif inp == '4':
        settings(downloader, config)
    elif inp == '5':
        backup(downloader, 'C:\\Users\\Administrator\\fanqie_down_backup')
    elif inp == '6':
        quit(0)
    else:
        download_novel(downloader, inp)

def main():
    print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & qxqycb')
    
    config = Config()
    downloader = NovelDownloader(config)
    check_backup()

    while True:
        loop(downloader, config)

if __name__ == "__main__":
    main()

