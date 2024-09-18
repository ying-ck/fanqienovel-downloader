import requests as req
import platform,time,os
from tqdm import tqdm
from tkinter import Tk

import init
from down import book,epub,html,latex,pdf,markdown
from utils import savejson,loadjson,select_save_directory
import config

def search() -> None:
    while True:
        # 使用新的API进行搜索
        key = input("请输入搜索关键词（直接Enter返回）：")
        if key == '':
            return
        url = f"https://api5-normal-lf.fqnovel.com/reading/bookapi/search/page/v/?query={key}&aid=1967&channel=0&os_version=0&device_type=0&device_platform=0&iid=466614321180296&passback={{(page-1)*10}}&version_code=999"
        response = req.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                books = data['data']
                if not books:
                    print("没有找到相关书籍。")
                    break
                for i, bok in enumerate(books):
                    print(f"{i + 1}. 名称：{bok['book_data'][0]['book_name']} 作者：{bok['book_data'][0]['author']} ID：{bok['book_data'][0]['book_id']} 字数：{bok['book_data'][0]['word_number']}")
                while True:
                    choice_ = input("请选择一个结果, 输入 r 以重新搜索：")
                    if choice_ == "r":
                        break
                    elif choice_.isdigit() and 1 <= int(choice_) <= len(books):
                        chosen_book = books[int(choice_) - 1]
                        if not download(chosen_book['book_id']):
                            print('下载失败')
                    else:
                        print("输入无效，请重新输入。")
            else:
                print("输入无效，请重新输入。")
                print("搜索出错，错误码：", data['code'])
                break
        else:
            print("请求失败，状态码：", response.status_code)
            break



def download(book_id:str) -> bool:
    if book_id[:4]=='http':
        book_id=book_id.split('?')[0].split('/')[-1]
    try:
        records=loadjson(config.record_path)
        if book_id not in records:
            records.append(book_id)
            savejson(config.record_path,records)
        match config.config['save_mode']:
            case 3:
                success=epub.down_book_epub(book_id)
            case 4:
                success=html.down_book_html(book_id)
            case 5:
                success=latex.down_book_latex(book_id)
            case 6:
                success=pdf.down_book_pdf(book_id)
            case 7:
                success=markdown.down_book_md(book_id)
            case _:
                success=book.down_book(book_id)

        if not success:
            print('找不到此书')
            return False
        else:
            print('下载完成')
            return True
    except ValueError:
        print('请输入有效的选项或书籍ID。')
        return False


def update() -> None:
    records=loadjson(config.record_path)
    for book_id in tqdm(records):
        ok=download(book_id)
        if not ok:
            records.remove(book_id)
    savejson(config.record_path,records)
    print('更新完成')

def get_input(prompt: str, default: str = '') -> str:
    """获取输入，如果输入为空则返回默认值"""
    tmp = input(prompt)
    return tmp if tmp != '' else default

def update_delay() -> None:
    """更新下载间隔随机延迟"""
    print('由于延迟过小造成的后果请自行负责。\n请输入下载间隔随机延迟的')
    config.config['delay'][0] = int(get_input(f'下限（当前为{config.config["delay"][0]}）（毫秒）：', str(config.config['delay'][0])))
    config.config['delay'][1] = int(get_input(f'上限（当前为{config.config["delay"][1]}）（毫秒）：', str(config.config['delay'][1])))

def update_save_mode() -> None:
    """更新小说保存方式"""
    print('请选择：1.保存为单个 txt 2.分章保存 3.保存为 epub 4.保存为 HTML 网页格式 5.保存为 LaTeX 6.保存为PDF 7.保存为md')
    inp3 = input()
    match inp3:
        case '1' | '2' | '3' | '4' | '5' | '6' | '7':
            config.config['save_mode'] = int(inp3)
        case _:
            print('请正确输入!')
            return

def setting() -> None:
    print('请选择项目：1.正文段首占位符 2.章节下载间隔延迟 3.小说保存路径 4.小说保存方式 5.重置配置文件')
    inp2 = input()

    match inp2:
        case '1':
            # 更新正文段首占位符
            config.config['kgf'] = get_input(f'请输入正文段首占位符(当前为"{config.config["kgf"]}")(直接Enter不更改)：', config.config['kgf'])
            config.config['kg'] = int(get_input(f'请输入正文段首占位符数（当前为{config.config["kg"]}）：', str(config.config['kg'])))
        case '2':
            update_delay()
        case '3':
            print('tip:设置为当前目录点取消')
            time.sleep(1)
            config.config['save_path'] = select_save_directory()
        case '4':
            update_save_mode()
        case '5':
            os.removedirs(config.config_path)
            init.init_config()
        case _:
            print('请正确输入!')
            return

    savejson(config.config_path, config.config)
    print('设置完成')

def multiDownload() -> None:
    urls_path='urls.txt'  # 定义文件名
    if not os.path.exists(urls_path):
        print(f"未找到'{urls_path}'，将为您创建一个新的文件。")
        with open(urls_path,'w',encoding='UTF-8') as file:
            file.write("# 请输入小说链接，一行一个\n")
    print(f"'{urls_path}' 已存在。请在文件中输入小说链接，一行一个。")

    # 使用默认文本编辑器打开urls.txt文件供用户编辑
    root=Tk()
    root.withdraw()  # 隐藏主窗口
    root.update()  # 更新Tkinter的事件循环，确保窗口被隐藏

    if platform.system()=="Windows":
        # Windows系统使用os.startfile
        os.startfile(urls_path)
    elif platform.system()=="Darwin":
        # macOS系统使用open命令
        os.system(f"open -a TextEdit {urls_path}")
    else:
        # 其他系统使用默认文本编辑器
        os.system(f"xdg-open {urls_path}")

    print("输入完成后请保存并关闭文件，然后按Enter键继续...")
    input()

    # 读取urls.txt文件中的链接
    with open(urls_path,'r',encoding='UTF-8') as file:
        content=file.read()
        urls=content.replace(' ','').split('\n')

    # 开始批量下载
    for url in urls:
        if url[0]!='#':
            print(f'开始下载{url}')
            ok=download(url)
            if not ok:
                print(f'{url} 下载失败。')
            else:
                print(f'{url} 下载完成。')

