import time, os, json, random
from dataclasses import dataclass
from enum import Enum

headers_lib = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.47'}
]
headers = random.choice(headers_lib)

# Use absolute paths based on script location
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, 'data')
bookstore_dir = os.path.join(data_dir, 'bookstore')
record_path = os.path.join(data_dir, 'record.json')
config_path = os.path.join(data_dir, 'config.json')
cookie_path = os.path.join(data_dir, 'cookie.json')
charset_path = os.path.join(script_dir, 'charset.json')

with open(charset_path, 'r', encoding='UTF-8') as f:
    charset = json.load(f)
CODE = [[58344, 58715], [58345, 58716]]


class SaveMode(Enum):
    SINGLE_TXT = 1
    SPLIT_TXT = 2
    EPUB = 3
    HTML = 4
    LATEX = 5


@dataclass
class Config:
    kg: int = 0
    kgf: str = '　'
    delay: list[int] = None
    save_path: str = ''
    save_mode: SaveMode = SaveMode.SINGLE_TXT
    space_mode: str = 'halfwidth'
    xc: int = 1

    def __post_init__(self):
        if self.delay is None:
            self.delay = [50, 150]

    def update_placeholder(self):
        tmp = input('请输入正文段首占位符(当前为"%s")(直接Enter不更改)：' % self.kgf)
        if tmp != '':
            self.kgf = tmp
        self.kg = int(input('请输入正文段首占位符数（当前为%d）：' % self.kg))

    def update_delay(self):
        print('由于迟过小造成的后果请自行负责。\n请输入下载间隔随机延迟')
        self.delay[0] = int(input('下限（当前为%d）（毫秒）：' % self.delay[0]))
        self.delay[1] = int(input('上限（当前为%d）（毫秒）：' % self.delay[1]))

    def update_save_path(self):
        print('tip:设置为当前目录点取消')
        time.sleep(1)
        path = input("\n请输入保存目录的完整路径:\n(直接按Enter使用当前目录)\n").strip()
        if path == "":
            self.save_path = os.getcwd()
        else:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                    self.save_path = path
                except:
                    print("无法创建目录，将使用当前目录")
                    self.save_path = os.getcwd()
            else:
                self.save_path = path

    def update_save_mode(self):
        print('请选择：1.保存为单个 txt 2.分章保存 3.保存为 epub 4.保存为 HTML 网页格式 5.保存为 LaTeX')
        inp3 = input()
        try:
            self.save_mode = SaveMode(int(inp3))
        except ValueError:
            print('请正确输入!')

    def update_threads(self):
        self.xc = int(input('请输入下载线程数：'))

    def save_config(self, config_path: str):
        # Save config
        with open(config_path, 'w', encoding='UTF-8') as f:
            json.dump({
                'kg': self.kg,
                'kgf': self.kgf,
                'delay': self.delay,
                'save_path': self.save_path,
                'save_mode': self.save_mode.value,
                'space_mode': self.space_mode,
                'xc': self.xc
            }, f)
        print('设置完成')