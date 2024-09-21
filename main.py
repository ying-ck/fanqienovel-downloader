# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import requests as req
from kivy.graphics import Color, Rectangle
from kivy.properties import ObjectProperty

from kivy.core.text import LabelBase
import os
import json
import random
import time
from tqdm import tqdm
from lxml import etree
from bs4 import BeautifulSoup

CODE = [[58344, 58715], [58345, 58716]]
charset = json.loads(
    '[["D","在","主","特","家","军","然","表","场","4","要","只","v","和","?","6","别","还","g","现","儿","岁","?","?","此","象","月","3","出","战","工","相","o","男","直","失","世","F","都","平","文","什","V","O","将","真","T","那","当","?","会","立","些","u","是","十","张","学","气","大","爱","两","命","全","后","东","性","通","被","1","它","乐","接","而","感","车","山","公","了","常","以","何","可","话","先","p","i","叫","轻","M","士","w","着","变","尔","快","l","个","说","少","色","里","安","花","远","7","难","师","放","t","报","认","面","道","S","?","克","地","度","I","好","机","U","民","写","把","万","同","水","新","没","书","电","吃","像","斯","5","为","y","白","几","日","教","看","但","第","加","候","作","上","拉","住","有","法","r","事","应","位","利","你","声","身","国","问","马","女","他","Y","比","父","x","A","H","N","s","X","边","美","对","所","金","活","回","意","到","z","从","j","知","又","内","因","点","Q","三","定","8","R","b","正","或","夫","向","德","听","更","?","得","告","并","本","q","过","记","L","让","打","f","人","就","者","去","原","满","体","做","经","K","走","如","孩","c","G","给","使","物","?","最","笑","部","?","员","等","受","k","行","一","条","果","动","光","门","头","见","往","自","解","成","处","天","能","于","名","其","发","总","母","的","死","手","入","路","进","心","来","h","时","力","多","开","已","许","d","至","由","很","界","n","小","与","Z","想","代","么","分","生","口","再","妈","望","次","西","风","种","带","J","?","实","情","才","这","?","E","我","神","格","长","觉","间","年","眼","无","不","亲","关","结","0","友","信","下","却","重","己","老","2","音","字","m","呢","明","之","前","高","P","B","目","太","e","9","起","稜","她","也","W","用","方","子","英","每","理","便","四","数","期","中","C","外","样","a","海","们","任"],["s","?","作","口","在","他","能","并","B","士","4","U","克","才","正","们","字","声","高","全","尔","活","者","动","其","主","报","多","望","放","h","w","次","年","?","中","3","特","于","十","入","要","男","同","G","面","分","方","K","什","再","教","本","己","结","1","等","世","N","?","说","g","u","期","Z","外","美","M","行","给","9","文","将","两","许","张","友","0","英","应","向","像","此","白","安","少","何","打","气","常","定","间","花","见","孩","它","直","风","数","使","道","第","水","已","女","山","解","d","P","的","通","关","性","叫","儿","L","妈","问","回","神","来","S","","四","望","前","国","些","O","v","l","A","心","平","自","无","军","光","代","是","好","却","c","得","种","就","意","先","立","z","子","过","Y","j","表","","么","所","接","了","名","金","受","J","满","眼","没","部","那","m","每","车","度","可","R","斯","经","现","门","明","V","如","走","命","y","6","E","战","很","上","f","月","西","7","长","夫","想","话","变","海","机","x","到","W","一","成","生","信","笑","但","父","开","内","东","马","日","小","而","后","带","以","三","几","为","认","X","死","员","目","位","之","学","远","人","音","呢","我","q","乐","象","重","对","个","被","别","F","也","书","稜","D","写","还","因","家","发","时","i","或","住","德","当","o","l","比","觉","然","吃","去","公","a","老","亲","情","体","太","b","万","C","电","理","?","失","力","更","拉","物","着","原","她","工","实","色","感","记","看","出","相","路","大","你","候","2","和","?","与","p","样","新","只","便","最","不","进","T","r","做","格","母","总","爱","身","师","轻","知","往","加","从","?","天","e","H","?","听","场","由","快","边","让","把","任","8","条","头","事","至","起","点","真","手","这","难","都","界","用","法","n","处","下","又","Q","告","地","5","k","t","岁","有","会","果","利","民"]]')
headers_lib = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'},
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.47'}
]

headers = headers_lib[random.randint(0, len(headers_lib) - 1)]


def get_cookie(zj, t=0):
    global cookie
    bas = 1000000000000000000
    if t == 0:
        for i in range(random.randint(bas * 6, bas * 8), bas * 9):
            time.sleep(random.randint(50, 150) / 1000)
            cookie = 'novel_web_id=' + str(i)
            if len(down_text(zj, 2)) > 200:
                with open(cookie_path, 'w', encoding='UTF-8') as f:
                    json.dump(cookie, f)
                return 's'
    else:
        cookie = t
        if len(down_text(zj, 2)) > 200:
            return 's'
        else:
            return 'err'

def down_zj(it):
    an = {}
    ele = etree.HTML(req.get('https://fanqienovel.com/page/' + str(it), headers=headers).text)
    a = ele.xpath('//div[@class="chapter"]/div/a')
    for i in range(len(a)):
        an[a[i].text] = a[i].xpath('@href')[0].split('/')[-1]
    if ele.xpath('//h1/text()') == []:
        return ['err', 0, 0]
    return [ele.xpath('//h1/text()')[0], an, ele.xpath('//span[@class="info-label-yellow"]/text()')]

def interpreter(uni, mode):
    bias = uni - CODE[mode][0]
    if bias < 0 or bias >= len(charset[mode]) or charset[mode][bias] == '?':
        return chr(uni)
    return charset[mode][bias]

def str_interpreter(n, mode):
    s = ''
    for i in range(len(n)):
        uni = ord(n[i])
        if CODE[mode][0] <= uni <= CODE[mode][1]:
            s += interpreter(uni, mode)
        else:
            s += n[i]
    return s

def down_text(it, mod=1):
    global cookie
    headers2 = headers
    headers2['cookie'] = cookie
    f = False
    while True:
        try:
            res = req.get('https://fanqienovel.com/reader/' + str(it), headers=headers2)
            n = '\n'.join(etree.HTML(res.text).xpath('//div[@class="muye-reader-content noselect"]//p/text()'))
            break
        except:
            if mod == 2:
                return ('err')
            f = True
            time.sleep(0.4)
    if mod == 1:
        s = str_interpreter(n, 0)
    else:
        s = n
    try:
        if mod == 1:
            return s, f
        else:
            return s
    except:
        s = s[6:]
        tmp = 1
        a = ''
        for i in s:
            if i == '<':
                tmp += 1
            elif i == '>':
                tmp -= 1
            elif tmp == 0:
                a += i
            elif tmp == 1 and i == 'p':
                a = (a + '\n').replace('\n\n', '\n')
        return a, f

def down_text_old(it, mod=1):
    global cookie
    headers2 = headers
    headers2['cookie'] = cookie
    f = False
    while True:
        try:
            res = req.get('https://fanqienovel.com/api/reader/full?itemId=' + str(it), headers=headers2)
            n = json.loads(res.text)['data']['chapterData']['content']
            break
        except:
            if mod == 2:
                return ('err')
            f = True
            time.sleep(0.4)
    if mod == 1:
        s = str_interpreter(n, 0)
    else:
        s = n
    try:
        if mod == 1:
            return '\n'.join(etree.HTML(s).xpath('//p/text()')), f
        else:
            return '\n'.join(etree.HTML(s).xpath('//p/text()'))
    except:
        s = s[6:]
        tmp = 1
        a = ''
        for i in s:
            if i == '<':
                tmp += 1
            elif i == '>':
                tmp -= 1
            elif tmp == 0:
                a += i
            elif tmp == 1 and i == 'p':
                a = (a + '\n').replace('\n\n', '\n')
        return a, f

def sanitize_filename(filename):
    illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    illegal_chars_rep = ['＜', '＞', '：', '＂', '／', '＼', '｜', '？', '＊']
    for i in range(len(illegal_chars)):
        filename = filename.replace(illegal_chars[i], illegal_chars_rep[i])
    return filename

script_dir = ''

# 设置data文件夹的路径
data_dir = os.path.join(script_dir, 'data')

# 检查data文件夹是否存在，如果不存在则创建
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 设置bookstore文件夹的路径
bookstore_dir = os.path.join(data_dir, 'bookstore')

# 检查bookstore文件夹是否存在，如果不存在则创建
if not os.path.exists(bookstore_dir):
    os.makedirs(bookstore_dir)

# 更新record.json和config.json的文件路径
record_path = os.path.join(data_dir, 'record.json')
config_path = os.path.join(data_dir, 'config.json')

config_path = os.path.join(data_dir, 'config.json')
reset = {'kg': 0, 'kgf': '　', 'delay': [50, 150], 'save_path': '', 'save_mode': 1, 'space_mode': 'halfwidth'}

config_path = os.path.join(data_dir, 'config.json')
reset = {'kg': 0, 'kgf': '　', 'delay': [50, 150], 'save_path': '', 'save_mode': 1, 'space_mode': 'halfwidth'}
if not os.path.exists(config_path):
    if os.path.exists('config.json'):
        os.replace('config.json', config_path)
    else:
        config = reset
        with open(config_path, 'w', encoding='UTF-8') as f:
            json.dump(reset, f)
else:
    with open(config_path, 'r', encoding='UTF-8') as f:
        config = json.load(f)
for i in reset:
    if not i in config:
        config[i] = reset[i]

# 检查并创建记录文件record.json
record_path = os.path.join(data_dir, 'record.json')
if not os.path.exists(record_path):
    if os.path.exists('record.json'):
        os.replace('record.json', record_path)
    else:
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump([], f)

print('正在获取cookie')
cookie_path = os.path.join(data_dir, 'cookie.json')
tzj = int(random.choice(list(down_zj(7143038691944959011)[1].values())[21:]))
tmod = 0
if os.path.exists(cookie_path):
    with open(cookie_path, 'r', encoding='UTF-8') as f:
        cookie = json.load(f)
    tmod = 1
if tmod == 0 or get_cookie(tzj, cookie) == 'err':
    get_cookie(tzj)
print('成功')


class FanqienovelApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical')

        # 显示选项
        option_label = Label(text='请选择操作：', font_name='SimHei')
        main_layout.add_widget(option_label)

        update_button = Button(text='1. 更新小说', font_name='SimHei')
        update_button.bind(on_release=self.update_novel)
        main_layout.add_widget(update_button)

        search_button = Button(text='2. 搜索', font_name='SimHei')
        search_button.bind(on_release=self.show_search_interface)
        main_layout.add_widget(search_button)

        batch_download_button = Button(text='3. 批量下载', font_name='SimHei')
        batch_download_button.bind(on_release=self.batch_download)
        main_layout.add_widget(batch_download_button)

        settings_button = Button(text='4. 设置', font_name='SimHei')
        settings_button.bind(on_release=self.show_settings)
        main_layout.add_widget(settings_button)

        # 添加直接下载输入框选项
        self.direct_download_input = TextInput(hint_text='输入书的 id 或链接直接下载', font_name='SimHei')
        main_layout.add_widget(self.direct_download_input)

        # 初始化确定按钮并设置不透明度为 0（不可见）
        self.confirm_button = Button(text='确定', font_name='SimHei', size_hint=(None, None))
        self.confirm_button.opacity = 0
        self.confirm_button.bind(on_release=self.direct_download)
        main_layout.add_widget(self.confirm_button)

        # 监听输入框内容变化
        self.direct_download_input.bind(text=self.on_input_change)

        return main_layout

    def on_input_change(self, instance, value):
        if value:
            # 如果输入框有内容，设置确定按钮不透明度为 1（可见）
            self.confirm_button.opacity = 1
        else:
            # 如果输入框没有内容，设置确定按钮不透明度为 0（不可见）
            self.confirm_button.opacity = 0

    def update_novel(self, instance):
        # 实现更新小说的逻辑
        self.root.clear_widgets()
        update_layout = BoxLayout(orientation='vertical')
        back_button = Button(text='◀', size_hint=(None, None), size=(30, 30), font_name='SimHei', on_release=self.return_to_main)
        back_button.pos_hint = {'x': 0, 'y': self.root.height - back_button.height}
        update_layout.add_widget(back_button)
        update_label = Label(text='正在更新小说...', font_name='SimHei')
        update_layout.add_widget(update_label)
        self.root.add_widget(update_layout)

    def show_search_interface(self, instance):
        # 显示搜索界面
        self.root.clear_widgets()
        search_layout = BoxLayout(orientation='vertical')
        back_button = Button(text='◀', size_hint=(None, None), size=(30, 30), font_name='SimHei', on_release=self.return_to_main)
        back_button.pos_hint = {'x': 0, 'y': self.root.height - back_button.height}
        search_layout.add_widget(back_button)
        # 搜索输入框
        self.search_input = TextInput(hint_text='输入关键词或书的 ID', font_name='SimHei')
        search_layout.add_widget(self.search_input)

        # 搜索按钮
        search_button = Button(text='搜索', font_name='SimHei')
        search_button.bind(on_release=self.perform_search)
        search_layout.add_widget(search_button)

        # 结果显示标签
        self.result_label = Label(text='', font_name='SimHei')
        search_layout.add_widget(self.result_label)

        self.root.add_widget(search_layout)

    def perform_search(self, instance):
        query = self.search_input.text
        result = self.search(query)
        self.result_label.text = result

    def search(self, key):
        if key == '':
            return '请输入有效的关键词或书的 ID'
        url = f"https://api5-normal-lf.fqnovel.com/reading/bookapi/search/page/v/?query={key}&aid=1967&channel=0&os_version=0&device_type=0&device_platform=0&iid=466614321180296&passback={{(page-1)*10}}&version_code=999"
        response = req.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                books = data['data']
                if not books:
                    return "没有找到相关书籍。"
                result_str = ""
                for i, book in enumerate(books):
                    result_str += f"{i + 1}. 名称：{book['book_data'][0]['book_name']} 作者：{book['book_data'][0]['author']} ID：{book['book_data'][0]['book_id']} 字数：{book['book_data'][0]['word_number']}\n"
                return result_str
            else:
                return f"搜索出错，错误码：{data['code']}"
        else:
            return f"请求失败，状态码：{response.status_code}"

    def batch_download(self, instance):
        # 实现批量下载的逻辑
        self.root.clear_widgets()
        download_layout = BoxLayout(orientation='vertical')
        back_button = Button(text='◀', size_hint=(None, None), size=(30, 30), font_name='SimHei', on_release=self.return_to_main)
        back_button.pos_hint = {'x': 0, 'y': self.root.height - back_button.height}
        download_layout.add_widget(back_button)
        download_label = Label(text='正在进行批量下载...', font_name='SimHei')
        download_layout.add_widget(download_label)
        self.root.add_widget(download_layout)

    def show_settings(self, instance):
        # 实现设置界面的逻辑
        self.root.clear_widgets()
        settings_layout = BoxLayout(orientation='vertical')
        back_button = Button(text='◀', size_hint=(None, None), size=(30, 30), font_name='SimHei', on_release=self.return_to_main)
        back_button.pos_hint = {'x': 0, 'y': self.root.height - back_button.height}
        settings_layout.add_widget(back_button)
        settings_label = Label(text='设置界面', font_name='SimHei')
        settings_layout.add_widget(settings_label)
        self.root.add_widget(settings_layout)

    def return_to_main(self, instance):
        self.root.clear_widgets()
        main_layout = BoxLayout(orientation='vertical')
        option_label = Label(text='请选择操作：', font_name='SimHei')
        main_layout.add_widget(option_label)
        update_button = Button(text='1. 更新小说', font_name='SimHei')
        update_button.bind(on_release=self.update_novel)
        main_layout.add_widget(update_button)
        search_button = Button(text='2. 搜索', font_name='SimHei')
        search_button.bind(on_release=self.show_search_interface)
        main_layout.add_widget(search_button)
        batch_download_button = Button(text='3. 批量下载', font_name='SimHei')
        batch_download_button.bind(on_release=self.batch_download)
        main_layout.add_widget(batch_download_button)
        settings_button = Button(text='4. 设置', font_name='SimHei')
        settings_button.bind(on_release=self.show_settings)
        main_layout.add_widget(settings_button)
        # 重新添加直接下载输入框选项
        self.direct_download_input = TextInput(hint_text='输入书的 id直接下载', font_name='SimHei')
        main_layout.add_widget(self.direct_download_input)
        # 重新添加确定按钮并设置初始状态为不可见
        self.confirm_button = Button(text='确定', font_name='SimHei', size_hint=(None, None))
        self.confirm_button.opacity = 0
        self.confirm_button.bind(on_release=self.direct_download)
        main_layout.add_widget(self.confirm_button)
        self.root.add_widget(main_layout)

    def direct_download(self, instance):
        input_text = self.direct_download_input.text
        if not input_text:
            print("请输入有效的书籍 ID")
            return

        try:
            name, zj, zt = down_zj(input_text)
            if name == 'err':
                print("下载失败，请检查输入的 ID 或链接是否正确")
                return

            zt = zt[0]

            safe_name = sanitize_filename(name)
            book_dir = os.path.join(script_dir, safe_name)
            print('\n开始下载《%s》，状态‘%s’' % (name, zt))
            book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

            if os.path.exists(book_json_path):
                with open(book_json_path, 'r', encoding='UTF-8') as json_file:
                    ozj = json.load(json_file)
            else:
                ozj = {}

            cs = 0
            tcs = 0
            pbar = tqdm(total=len(zj))
            for i in zj:
                f = False
                if i in ozj:
                    try:
                        int(ozj[i])
                        f = True
                    except:
                        zj[i] = ozj[i]
                else:
                    f = True
                if f:
                    tqdm.write(f'下载 {i}')
                    zj[i], st = down_text(zj[i])
                    time.sleep(random.randint(1, 5) / 1000)
                    if st:
                        tcs += 1
                        if tcs > 7:
                            tcs = 0
                            get_cookie('temp_value')
                    cs += 1
                    if cs >= 5:
                        cs = 0
                        with open(book_json_path, 'w', encoding='UTF-8') as json_file:
                            json.dump(zj, json_file, ensure_ascii=False)
                pbar.update(1)

            with open(book_json_path, 'w', encoding='UTF-8') as json_file:
                json.dump(zj, json_file, ensure_ascii=False)

            fg = '\n' + config['kgf'] * config['kg']
            if config['save_mode'] == 1:
                text_file_path = os.path.join(config['save_path'], safe_name + '.txt')
                with open(text_file_path, 'w', encoding='UTF-8') as text_file:
                    for chapter_title in zj:
                        text_file.write('\n' + chapter_title + fg)
                        if config['space_mode'] == 'halfwidth':
                            text_file.write(zj[chapter_title] + '\n')
                        else:
                            text_file.write(zj[chapter_title].replace('\n', fg) + '\n')
            elif config['save_mode'] == 2:
                text_dir_path = os.path.join(config['save_path'], safe_name)
                if not os.path.exists(text_dir_path):
                    os.makedirs(text_dir_path)
                for chapter_title in zj:
                    text_file_path = os.path.join(text_dir_path, sanitize_filename(chapter_title) + '.txt')
                    with open(text_file_path, 'w', encoding='UTF-8') as text_file:
                        text_file.write(fg)
                        if config['space_mode'] == 'halfwidth':
                            text_file.write(zj[chapter_title] + '\n')
                        else:
                            text_file.write(zj[chapter_title].replace('\n', fg) + '\n')
            else:
                print('保存模式出错！')

            print(f"《{name}》下载完成，状态：{zt}")

        except Exception as e:
            print(f"下载过程中出现错误: {str(e)}")

        finally:
            self.direct_download_input.text = ''  # 清空输入框




if __name__ == '__main__':
    FanqienovelApp().run()