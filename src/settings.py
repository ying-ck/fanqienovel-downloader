import time, os, json
from dataclasses import dataclass
from enum import Enum


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