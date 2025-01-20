# -*- coding: utf-8 -*-
import requests as req
from lxml import etree
from lxml import html
from tkinter import Tk, filedialog
from ebooklib import epub
from tqdm import tqdm
from bs4 import BeautifulSoup
import json, time, random, os, platform, shutil
import concurrent.futures
import threading
import asyncio
import sys

try:
    import edge_tts
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False

class NetworkManager:
    def __init__(self):
        self.min_threads = 1
        self.max_threads = 10
        self.current_threads = 1
        self.network_check_interval = 30
        self.last_check_time = 0
        self.retry_delays = [1, 2, 4, 8, 16]
        self.last_network_score = 0
        self.session = req.Session()
        self.session.mount('http://', req.adapters.HTTPAdapter(max_retries=3))
        self.session.mount('https://', req.adapters.HTTPAdapter(max_retries=3))
        
        self.session.headers.update({
            'User-Agent': random.choice(headers_lib)['User-Agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        })
        
    def get_session(self):
        return self.session
        
    def make_request(self, url, method='GET', **kwargs):
        max_retries = kwargs.pop('max_retries', 3)
        retry_delay = kwargs.pop('retry_delay', 1)
        timeout = kwargs.pop('timeout', 10)
        
        for retry in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except req.Timeout:
                print(f"请求超时,重试第{retry + 1}次...")
            except req.RequestException as e:
                print(f"网络错误: {e},重试第{retry + 1}次...")
            except Exception as e:
                print(f"未知错误: {e},重试第{retry + 1}次...")
                
            if retry < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2
                
        raise req.RequestException(f"请求失败,已重试{max_retries}次")
        
    def check_network_status(self):
        try:
            start_time = time.time()
            response = self.make_request('https://fanqienovel.com', timeout=5)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                if latency < 0.5:
                    score = 100
                elif latency < 1:
                    score = 80
                elif latency < 2:
                    score = 60
                elif latency < 3:
                    score = 40
                else:
                    score = 20
                self.last_network_score = score
                return score
            return 0
        except:
            self.last_network_score = 0
            return 0
            
    def display_network_status(self):
        score = self.check_network_status()
        print(f"网络状态: {'良好' if score >= 60 else '一般' if score >= 40 else '较差'}")
        
    def close(self):
        try:
            self.session.close()
        except:
            pass
        
    def adjust_threads(self):
        current_time = time.time()
        if current_time - self.last_check_time >= self.network_check_interval:
            network_score = self.check_network_status()
            self.last_check_time = current_time
            
            if network_score >= 80:
                self.current_threads = min(self.current_threads + 1, self.max_threads)
            elif network_score <= 40:
                self.current_threads = max(self.current_threads - 1, self.min_threads)
            
            return self.current_threads

class ConfigChecker:
    def __init__(self):
        self.check_results = {
            'config_file': False,
            'config_format': False,
            'required_fields': False,
            'value_types': False,
            'value_ranges': False,
            'directories': False
        }
        self.required_fields = {
            'kg': int,
            'kgf': str,
            'delay': list,
            'save_path': str,
            'save_mode': int,
            'space_mode': str,
            'xc': int,
            'enable_chapter_numbering': bool,
            'auto_retry': bool,
            'max_retries': int,
            'timeout': int,
            'version': str
        }
        self.value_ranges = {
            'kg': (0, 10),
            'save_mode': (1, 5),
            'xc': (1, 32),
            'max_retries': (1, 10),
            'timeout': (1, 60)
        }
        
    def check_config_file(self, config_path):
        try:
            self.check_results['config_file'] = os.path.exists(config_path)
            return self.check_results['config_file']
        except Exception as e:
            print(f"检查配置文件时出错: {e}")
            return False
            
    def check_config_format(self, config):
        try:
            if isinstance(config, dict):
                self.check_results['config_format'] = True
                return True
            return False
        except Exception:
            return False
            
    def check_required_fields(self, config):
        try:
            for field, field_type in self.required_fields.items():
                if field not in config or not isinstance(config[field], field_type):
                    return False
            self.check_results['required_fields'] = True
            return True
        except Exception:
            return False
            
    def check_value_ranges(self, config):
        try:
            for field, (min_val, max_val) in self.value_ranges.items():
                if field in config:
                    value = config[field]
                    if not (min_val <= value <= max_val):
                        return False
            self.check_results['value_ranges'] = True
            return True
        except Exception:
            return False
            
    def check_directories(self, config):
        try:
            required_dirs = ['data', 'bookstore']
            for dir_name in required_dirs:
                dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name)
                if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
                    return False
            self.check_results['directories'] = True
            return True
        except Exception:
            return False
            
    def perform_check(self, config_path, config):
        # 检查是否是首次运行（data文件夹不存在）
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        if not os.path.exists(data_dir):
            print("\n首次运行程序，跳过配置检查...")
            return True
            
        checks = [
            (self.check_config_file(config_path), "配置文件检查"),
            (self.check_config_format(config), "配置格式检查"),
            (self.check_required_fields(config), "必需字段检查"),
            (self.check_value_ranges(config), "数值范围检查"),
            (self.check_directories(config), "目录检查")
        ]
        
        print("\n配置检查结果:")
        all_passed = True
        for result, description in checks:
            status = "通过" if result else "失败"
            print(f"{description}: {status}")
            if not result:
                all_passed = False
                
        if all_passed:
            print("\n所有配置检查通过！")
        else:
            print("\n配置检查未完全通过，程序可能无法正常运行。")
            
        return all_passed

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

zj = {}  # 添加全局变量声明

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
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}
    response = req.get('https://fanqienovel.com/page/' + str(it), headers=headers)
    if response.status_code == 200:
        time.sleep(1)
        ele = etree.HTML(response.text)

        title_xpath_result = ele.xpath('//h1/text()')
        if not title_xpath_result:
            return ['err', 0, 0]

        a = ele.xpath('//div[@class="chapter"]/div/a')
        for i in range(len(a)):
            an[a[i].text] = a[i].xpath('@href')[0].split('/')[-1]

        return [title_xpath_result[0], an, ele.xpath('//span[@class="info-label-yellow"]/text()')]
    else:
        print(f"网络请求失败，状态码: {response.status_code}，请检查网络连接或稍试。")
        return ['err', 0, 0]

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
    headers2 = headers.copy()
    headers2['cookie'] = cookie
    f = False
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            res = req.get('https://fanqienovel.com/reader/' + str(it), 
                         headers=headers2, 
                         timeout=10)
            ele = etree.HTML(res.text)

            n = '\n'.join(ele.xpath('//div[@class="muye-reader-content noselect"]//p/text()'))
            if not n:
                n = '\n'.join(ele.xpath('//div[@class="muye-reader-content muye-reader-story-content noselect"]//p/text()'))

            break
        except Exception as e:
            retry_count += 1
            if mod == 2:
                return 'err'
            f = True
            print(f"下载出错,正在重试({retry_count}/{max_retries}): {str(e)}")
            time.sleep(0.4 * retry_count)
    
    if retry_count >= max_retries:
        print("达到最大重试次数,下载失败")
        return ('err', True) if mod == 1 else 'err'
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

def download_chapter(chapter_title, chapter_id, ozj):
    global zj, cs, book_json_path, json
    f = False
    if chapter_title in ozj:
        try:
            int(ozj[chapter_title])
            f = True
        except:
            zj[chapter_title] = ozj[chapter_title]
    else:
        f = True
    if f:
        tqdm.write(f'下载 {chapter_title}')
        zj[chapter_title], st = down_text(chapter_id)
        time.sleep(random.randint(config['delay'][0], config['delay'][1]) / 1000)
        if st:
            tcs += 1
            if tcs > 7:
                tcs = 0
                get_cookie(tzj)
        cs += 1
        if cs >= 5:
            cs = 0
            with open(book_json_path, 'w', encoding='UTF-8') as json_file:
                json.dump(zj, json_file, ensure_ascii=False)
    return chapter_title

def down_book(it, chapter_range=""):
    global zj, cs, book_json_path, json
    name, zj, zt = down_zj(it)
    if name == 'err':
        return 'err'
    zt = zt[0]

    safe_name = sanitize_filename(name + chapter_range)
    book_dir = os.path.join(script_dir, safe_name)
    print(f'\n开始下载《{name}》，状态：{zt}')
    book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

    if os.path.exists(book_json_path):
        with open(book_json_path, 'r', encoding='UTF-8') as json_file:
            ozj = json.load(json_file)
    else:
        ozj = {}

    cs = 0
    tcs = 0
    tasks = []
    # 使用配置的线程数创建线程池
    if 'xc' in config:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['xc'])
    else:
        executor = concurrent.futures.ThreadPoolExecutor()
    pbar = tqdm(total=len(zj))
    for chapter_title, chapter_id in zj.items():
        tasks.append(executor.submit(download_chapter, chapter_title, chapter_id, ozj))
    for future in concurrent.futures.as_completed(tasks):
        chapter_title = future.result()
        pbar.update(1)

    with open(book_json_path, 'w', encoding='UTF-8') as json_file:
        json.dump(zj, json_file, ensure_ascii=False)

    # 获取作者信息和内容简介
    url = f'https://fanqienovel.com/page/{it}'
    response = req.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 获取小说名
    name_element = soup.find('h1')
    if name_element:
        name = name_element.text
    # 获取作者信息
    author_name_element = soup.find('div', class_='author-name')
    author_name = None
    if author_name_element:
        author_name = author_name_element.find('span', class_='author-name-text').text
    # 获取内容简介
    description = None
    description_element = soup.find('div', class_='page-abstract-content')
    if description_element:
        description = description_element.find('p').text

    fg = '\n' + config['kgf'] * config['kg']
    if config['save_mode'] == 1:
        text_file_path = os.path.join(config['save_path'], safe_name + '.txt')
        with open(text_file_path, 'w', encoding='UTF-8') as text_file:
            text_file.write(f'小说名：{name}\n作者：{author_name}\n内容简介：{description}\n')
            for chapter_title in zj:
                text_file.write('\n' + chapter_title + fg)
                if config['kg'] == 0:
                    text_file.write(zj[chapter_title] + '\n')
                else:
                    text_file.write(zj[chapter_title].replace('\n', fg) + '\n')
    elif config['save_mode'] == 2:
        text_dir_path = os.path.join(config['save_path'], safe_name)
        if not os.path.exists(text_dir_path):
            os.makedirs(text_dir_path)
        if config.get('enable_chapter_numbering', False):
            for index, chapter_title in enumerate(zj):
                new_chapter_title = f"第{index + 1}章 {chapter_title}"
                text_file_path = os.path.join(text_dir_path, sanitize_filename(new_chapter_title) + '.txt')
                with open(text_file_path, 'w', encoding='UTF-8') as text_file:
                    text_file.write(fg)
                    if config['kg'] == 0:
                        text_file.write(zj[chapter_title] + '\n')
                    else:
                        text_file.write(zj[chapter_title].replace('\n', fg) + '\n')
        else:
            for chapter_title in zj:
                text_file_path = os.path.join(text_dir_path, sanitize_filename(chapter_title) + '.txt')
                with open(text_file_path, 'w', encoding='UTF-8') as text_file:
                    text_file.write(fg)
                    if config['kg'] == 0:
                        text_file.write(zj[chapter_title] + '\n')
                    else:
                        text_file.write(zj[chapter_title].replace('\n', fg) + '\n')
    else:
        print('保存模式出错！')

    return zt

def download_chapter_epub(chapter_title, chapter_id):
    try:
        tqdm.write(f'下载 {chapter_title}')
        chapter_content, _ = down_text(chapter_id)
        if not chapter_content:  # 检查内容是否为空
            return chapter_title, None
        
        # 处理章节内容，替换换行符为HTML段落标签
        formatted_content = '</p><p>'.join(filter(None, chapter_content.split('\n')))
        time.sleep(random.randint(config['delay'][0], config['delay'][1]) / 1000)
        
        return chapter_title, formatted_content
    except Exception as e:
        tqdm.write(f'下载章节 {chapter_title} 时出错: {str(e)}')
        return chapter_title, None

def down_book_epub(it, chapter_range=""):
    global zj, cs, book_json_path, json
    name, zj, zt = down_zj(it)
    if name == 'err':
        return 'err'
    zt = zt[0]

    safe_name = sanitize_filename(name + chapter_range)
    print(f'\n开始下载《{name}》，状态"{zt}"')
    book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

    # 获取作者信息和内容简介
    url = f'https://fanqienovel.com/page/{it}'
    response = req.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 获取作者信息
    author_name_element = soup.find('div', class_='author-name')
    author_name = None
    if author_name_element:
        author_name = author_name_element.find('span', class_='author-name-text').text
    
    # 获取内容简介
    description = None
    description_element = soup.find('div', class_='page-abstract-content')
    if description_element:
        description = description_element.find('p').text

    # 创建epub书籍
    book = epub.EpubBook()
    book.set_identifier(f'fanqie-{it}')
    book.set_title(name)
    book.set_language('zh-CN')
    if author_name:
        book.add_author(author_name)
    
    # 添加CSS样式
    style = '''
        @namespace epub "http://www.idpf.org/2007/ops";
        body { font-family: "Noto Serif CJK SC", SimSun, serif; }
        h1 { text-align: center; margin: 1em 0; }
        p { text-indent: 2em; margin: 0.5em 0; }
    '''
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=style
    )
    book.add_item(nav_css)

    # 添加简介章节
    if description:
        intro = epub.EpubHtml(title='简介', file_name='intro.xhtml')
        intro.content = f'<h1>简介</h1><p>{description}</p>'
        book.add_item(intro)

    # 下载章节内容
    chapters = []
    cs = 0
    tcs = 0
    tasks = []
    
    if 'xc' in config:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['xc'])
    else:
        executor = concurrent.futures.ThreadPoolExecutor()
    
    pbar = tqdm(total=len(zj))
    
    # 保持章节顺序
    ordered_chapters = list(zj.items())
    for chapter_title, chapter_id in ordered_chapters:
        tasks.append(executor.submit(download_chapter_epub, chapter_title, chapter_id))
    
    # 等待所有任务完成并按顺序处理结果
    downloaded_chapters = {}
    for future in concurrent.futures.as_completed(tasks):
        chapter_title, chapter_content = future.result()
        if chapter_content:  # 确保内容不为空
            downloaded_chapters[chapter_title] = chapter_content
        pbar.update(1)
    
    # 按原始顺序创建章节
    for chapter_title, _ in ordered_chapters:
        if chapter_title in downloaded_chapters:
            chapter_content = downloaded_chapters[chapter_title]
            # 创建章节
            c = epub.EpubHtml(title=chapter_title, file_name=f'chapter_{len(chapters)+1}.xhtml')
            c.content = f'<h1>{chapter_title}</h1><p>{chapter_content}</p>'
            book.add_item(c)
            chapters.append(c)

    # 添加目录
    book.toc = [(epub.Section('目录'), chapters)]
    book.spine = ['nav'] + chapters if not description else ['nav', intro] + chapters
    
    # 添加默认NCX和Nav文件
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # 生成epub文件
    if not config['save_path']:
        config['save_path'] = script_dir
    epub.write_epub(os.path.join(config['save_path'], f'{safe_name}.epub'), book)

    return 's'

def down_book_html(it, chapter_range=""):
    global zj, cs, book_json_path, book_dir, json
    name, zj, zt = down_zj(it)
    if name == 'err':
        return 'err'
    zt = zt[0]

    safe_name = sanitize_filename(name + chapter_range)
    book_dir = os.path.join(script_dir, f"{safe_name}(html)")
    if not os.path.exists(book_dir):
        os.makedirs(book_dir)

    print('\n开始下载《%s》，状态' % (name, zt))
    book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

    existing_json_content = {}
    if os.path.exists(book_json_path):
        with open(book_json_path, 'r', encoding='UTF-8') as json_file:
            existing_json_content = json.load(json_file)

    # 获取作者信息和内容简介
    url = f'https://fanqienovel.com/page/{it}'
    response = req.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 获取小说名
    name_element = soup.find('h1')
    if name_element:
        name = name_element.text
    # 获取作者信息
    author_name_element = soup.find('div', class_='author-name')
    author_name = None
    if author_name_element:
        author_name = author_name_element.find('span', class_='author-name-text').text
    # 获取内容简介
    description = None
    description_element = soup.find('div', class_='page-abstract-content')
    if description_element:
        description = description_element.find('p').text

    # 生成目录 HTML 文件内容，添加 CSS 样式和响应式设计的 meta 标签，并包含小说名、作者和内容简介
    toc_content = f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>目录</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        ul {{
            list-style-type: none;
            padding: 0;
        }}
        li a {{
            color: #007bff;
            text-decoration: none;
        }}
        li a:hover {{
            text-decoration: underline;
        }}
        p {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
<h1>目录 - 小说名：{name}，作者：{author_name}</h1>
<p>内容简介：{description}</p>
<ul>
"""
    if config.get('enable_chapter_numbering', False):
        for index, chapter_title in enumerate(zj):
            toc_content += f"<li><a href='{index + 1}_{chapter_title}.html'>第{index + 1}章 {chapter_title}</a></li>"
    else:
        for chapter_title in zj:
            toc_content += f"<li><a href='{chapter_title}.html'>{chapter_title}</a></li>"
    toc_content += "</ul></body></html>"

    # 将目录内容写入文件
    with open(os.path.join(book_dir, "index.html"), "w", encoding='UTF-8') as toc_file:
        toc_file.write(toc_content)

    cs = 0
    tcs = 0
    tasks = []
    # 使用配置的线程数创建线程池
    if 'xc' in config:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['xc'])
    else:
        executor = concurrent.futures.ThreadPoolExecutor()
    pbar = tqdm(total=len(zj))
    for chapter_title, chapter_id in zj.items():
        tasks.append(executor.submit(download_chapter_html, chapter_title, chapter_id, existing_json_content))
    for future in concurrent.futures.as_completed(tasks):
        chapter_title = future.result()
        pbar.update(1)

    return 's'


def download_chapter_html(chapter_title, chapter_id, existing_json_content):
    global zj, cs, book_json_path, book_dir, json
    f = False
    if chapter_title in existing_json_content:
        try:
            int(existing_json_content[chapter_title])
            f = True
        except:
            zj[chapter_title] = existing_json_content[chapter_title]
    else:
        f = True
    if f:
        tqdm.write(f'下载 {chapter_title}')
        chapter_content, _ = down_text(chapter_id)
        time.sleep(random.randint(config['delay'][0], config['delay'][1]) / 1000)
        cs += 1

        # 每章都保存 JSON 文件
        existing_json_content[chapter_title] = chapter_content
        with open(book_json_path, 'w', encoding='UTF-8') as json_file:
            json.dump(existing_json_content, json_file, ensure_ascii=False)

        # 生成章节 HTML 文件内容，添加 CSS 样式、返回顶部按钮和装饰元素，同时保留换行符
        formatted_content = chapter_content.replace('\n', '<br/>')
        next_chapter_button = ""
        if len(zj) > list(zj.keys()).index(chapter_title) + 1:
            if config.get('enable_chapter_numbering', False):
                next_chapter_key = list(zj.keys())[list(zj.keys()).index(chapter_title) + 1]
                next_chapter_number = list(zj.keys()).index(next_chapter_key) + 1
                next_chapter_button = f"<button onclick=\"location.href='{next_chapter_number}_{next_chapter_key}.html'\">下一章</button>"
            else:
                next_chapter_key = list(zj.keys())[list(zj.keys()).index(chapter_title) + 1]
                next_chapter_button = f"<button onclick=\"location.href='{next_chapter_key}.html'\">下一章</button>"

        if config.get('enable_chapter_numbering', False):
            chapter_number = list(zj.keys()).index(chapter_title) + 1
            chapter_html_content = f"""
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{chapter_number}_{chapter_title}</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .content {{
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }}
        p {{
            text-indent: 2em;
            margin: 1em 0;
        }}
        .nav-buttons {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        button {{
            margin: 0 5px;
            padding: 8px 15px;
            border: none;
            border-radius: 3px;
            background: #2c3e50;
            color: white;
            cursor: pointer;
        }}
        button:hover {{
            background: #34495e;
        }}
        #toggle-mode {{
            position: fixed;
            top: 20px;
            right: 20px;
        }}
        .dark-mode {{
            background-color: #1a1a1a;
            color: #f0f0f0;
        }}
        .dark-mode .content {{
            background: #2d2d2d;
            color: #f0f0f0;
        }}
        .dark-mode button {{
            background: #4a4a4a;
        }}
        .dark-mode button:hover {{
            background: #5a5a5a;
        }}
    </style>
</head>
<body>
<div class="content">
    <h1>第{chapter_number}章 {chapter_title}</h1>
    <p>{formatted_content}</p>
    <a href="#" id="back-to-top">返回顶部</a>
</div>
<div class="nav-buttons">
    <button onclick="location.href='index.html'">目录</button>
    {next_chapter_button}
    <button onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">返回顶部</button>
    <button id="toggle-mode">切换模式</button>
</div>
<script>
    // 暗黑模式切换
    const toggleButton = document.getElementById('toggle-mode');
    const body = document.body;
    
    // 检查本地存储中的主题设置
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {{
        body.classList.add('dark-mode');
    }}
    
    toggleButton.addEventListener('click', () => {{
        body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', body.classList.contains('dark-mode'));
    }});
    
    // 添加键盘快捷键
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowLeft') {{
            // 上一章
            const prevButton = document.querySelector('.nav-buttons button:nth-child(1)');
            if (prevButton) prevButton.click();
        }} else if (e.key === 'ArrowRight') {{
            // 下一章
            const nextButton = document.querySelector('.nav-buttons button:nth-child(2)');
            if (nextButton) nextButton.click();
        }} else if (e.key === 'Home') {{
            // 返回顶部
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}
    }});
</script>
</body>
</html>
"""
            with open(os.path.join(book_dir, f"{chapter_number}_{chapter_title}.html"), "w", encoding='UTF-8') as chapter_file:
                chapter_file.write(chapter_html_content)
        else:
            chapter_html_content = f"""
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{chapter_title}</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .content {{
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            border-radius: 5px;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }}
        p {{
            text-indent: 2em;
            margin: 1em 0;
        }}
        .nav-buttons {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        button {{
            margin: 0 5px;
            padding: 8px 15px;
            border: none;
            border-radius: 3px;
            background: #2c3e50;
            color: white;
            cursor: pointer;
        }}
        button:hover {{
            background: #34495e;
        }}
        #toggle-mode {{
            position: fixed;
            top: 20px;
            right: 20px;
        }}
        .dark-mode {{
            background-color: #1a1a1a;
            color: #f0f0f0;
        }}
        .dark-mode .content {{
            background: #2d2d2d;
            color: #f0f0f0;
        }}
        .dark-mode button {{
            background: #4a4a4a;
        }}
        .dark-mode button:hover {{
            background: #5a5a5a;
        }}
    </style>
</head>
<body>
<div class="content">
    <h1>{chapter_title}</h1>
    <p>{formatted_content}</p>
    <a href="#" id="back-to-top">返回顶部</a>
</div>
<div class="nav-buttons">
    <button onclick="location.href='index.html'">目录</button>
    {next_chapter_button}
    <button onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})">返回顶部</button>
    <button id="toggle-mode">切换模式</button>
</div>
<script>
    // 暗黑模式切换
    const toggleButton = document.getElementById('toggle-mode');
    const body = document.body;
    
    // 检查本地存储中的主题设置
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {{
        body.classList.add('dark-mode');
    }}
    
    toggleButton.addEventListener('click', () => {{
        body.classList.toggle('dark-mode');
        localStorage.setItem('darkMode', body.classList.contains('dark-mode'));
    }});
    
    // 添加键盘快捷键
    document.addEventListener('keydown', (e) => {{
        if (e.key === 'ArrowLeft') {{
            // 上一章
            const prevButton = document.querySelector('.nav-buttons button:nth-child(1)');
            if (prevButton) prevButton.click();
        }} else if (e.key === 'ArrowRight') {{
            // 下一章
            const nextButton = document.querySelector('.nav-buttons button:nth-child(2)');
            if (nextButton) nextButton.click();
        }} else if (e.key === 'Home') {{
            // 返回顶部
            window.scrollTo({{top: 0, behavior: 'smooth'}});
        }}
    }});
</script>
</body>
</html>
"""
            with open(os.path.join(book_dir, f"{chapter_title}.html"), "w", encoding='UTF-8') as chapter_file:
                chapter_file.write(chapter_html_content)
    return chapter_title


def download_chapter_latex(chapter_title, chapter_id, existing_json_content):
    global zj, cs, book_json_path ,book_dir, json
    f = False
    if chapter_title in existing_json_content:
        try:
            int(existing_json_content[chapter_title])
            f = True
        except:
            zj[chapter_title] = existing_json_content[chapter_title]
    else:
        f = True
    if f:
        tqdm.write(f'下载 {chapter_title}')
        chapter_content, _ = down_text(chapter_id)
        time.sleep(random.randint(config['delay'][0], config['delay'][1]) / 1000)

        # 每章都保存 JSON 文件
        existing_json_content[chapter_title] = chapter_content
        with open(book_json_path, 'w', encoding='UTF-8') as json_file:
            json.dump(existing_json_content, json_file, ensure_ascii=False)

        # 将章节内容转换为 LaTeX 格式
        chapter_content = chapter_content.replace('\\', '\\textbackslash')
        chapter_content = chapter_content.replace('_', '\\_')
        chapter_content = chapter_content.replace('{', '\\{')
        chapter_content = chapter_content.replace('}', '\\}')
        chapter_content = chapter_content.replace('$', '\\$')
        chapter_content = chapter_content.replace('#', '\\#')
        chapter_content = chapter_content.replace('%', '\\%')
        chapter_content = chapter_content.replace('&', '\\&')
        chapter_content = chapter_content.replace('\n', '\n\n') # 段落分隔
        
        return f"\\chapter{{{chapter_title}}}\n{chapter_content}\n"
    return None


def down_book_latex(it, chapter_range=""):
    global zj, cs, book_json_path, book_dir, json
    name, zj, zt = down_zj(it)
    if name == 'err':
        return 'err'
    zt = zt[0]

    safe_name = sanitize_filename(name + chapter_range)

    print('\n开始下载《%s》，状态' % (name, zt))
    book_json_path = os.path.join(bookstore_dir, safe_name + '.json')

    existing_json_content = {}
    if os.path.exists(book_json_path):
        with open(book_json_path, 'r', encoding='UTF-8') as json_file:
            existing_json_content = json.load(json_file)

    # 获取作者信息和内容简介
    url = f'https://fanqienovel.com/page/{it}'
    response = req.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    # 获取小说名
    name_element = soup.find('h1')
    if name_element:
        name = name_element.text
    # 获取作者信息
    author_name_element = soup.find('div', class_='author-name')
    author_name = None
    if author_name_element:
        author_name = author_name_element.find('span', class_='author-name-text').text
    # 获取内容简介
    description = None
    description_element = soup.find('div', class_='page-abstract-content')
    if description_element:
        description = description_element.find('p').text

    latex_content = f"""\\documentclass[12pt,a4paper]{{ctexbook}}
\\usepackage{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{xeCJK}}
\\usepackage{{indentfirst}}

\\geometry{{top=2.54cm, bottom=2.54cm, left=3.18cm, right=3.18cm}}
\\setlength{{\\parindent}}{{2em}}

\\title{{{name}}}
\\author{{{author_name if author_name else '佚名'}}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents

\\chapter*{{内容简介}}
{description}

"""
    cs = 0
    tcs = 0
    tasks = []
    if 'xc' in config:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config['xc'])
    else:
        executor = concurrent.futures.ThreadPoolExecutor()
    pbar = tqdm(total=len(zj))
    for chapter_title, chapter_id in zj.items():
        tasks.append(executor.submit(download_chapter_latex, chapter_title, chapter_id, existing_json_content))
    for future in concurrent.futures.as_completed(tasks):
        chapter_title = future.result()
        pbar.update(1)

    latex_file_path = os.path.join(script_dir, f'{safe_name}.tex')
    with open(latex_file_path, 'w', encoding='UTF-8') as latex_file:
        latex_file.write(latex_content)

    return 's'


def select_save_directory():
    root = Tk()
    root.withdraw()
    return filedialog.askdirectory(title='请选择保存小说的文件夹')

def search():
    while True:
        key = input("请输入搜索关键词（直接Enter返回）：")
        if key == '':
            return 'b'
        url = f"https://api5-normal-lf.fqnovel.com/reading/bookapi/search/page/v/?query={key}&aid=1967&channel=0&os_version=0&device_type=0&device_platform=0&iid=466614321180296&passback={{(page-1)*10}}&version_code=999"
        response = req.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                books = data['data']
                if not books:
                    print("没有找到相关书籍。")
                    break
                for i, book in enumerate(books):
                    print(f"{i + 1}. 名称：{book['book_data'][0]['book_name']} 作者：{book['book_data'][0]['author']} ID：{book['book_data'][0]['book_id']} 字数：{book['book_data'][0]['word_number']}")
                while True:
                    choice_ = input("请选择一个结果, 输入 r 以重新搜索：")
                    if choice_ == "r":
                        break
                    elif choice_.isdigit() and 1 <= int(choice_) <= len(books):
                        chosen_book = books[int(choice_) - 1]
                        return chosen_book['book_data'][0]['book_id']
                    else:
                        print("输入无效，请重新输入。")
            else:
                print("搜索出错，错误码：", data['code'])
                break
        else:
            print("请求失败，状态码：", response.status_code)
            break

def book2down(inp):
    if str(inp)[:4] == 'http':
        inp = inp.split('?')[0].split('/')[-1]
    try:
        book_id = int(inp)
        # 检查record.json是否存在，不存在则创建
        if not os.path.exists(record_path):
            with open(record_path, 'w', encoding='UTF-8') as f:
                json.dump([], f)
        
        with open(record_path, 'r', encoding='UTF-8') as f:
            records = json.load(f)
        if book_id not in records:
            records.append(book_id)
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump(records, f)
            
        # 获取全局变量中的章节范围信息
        start_chapter = getattr(book2down, 'start_chapter', None)
        end_chapter = getattr(book2down, 'end_chapter', None)
        chapter_range = f"({start_chapter}~{end_chapter})" if start_chapter and end_chapter else ""
            
        if config['save_mode'] == 3:
            status = down_book_epub(book_id, chapter_range)
        elif config['save_mode'] == 4:
            status = down_book_html(book_id, chapter_range)
        elif config['save_mode'] == 5:
            status = down_book_latex(book_id, chapter_range)
        else:
            status = down_book(book_id, chapter_range)
            
        if hasattr(book2down, 'start_chapter'):
            delattr(book2down, 'start_chapter')
        if hasattr(book2down, 'end_chapter'):
            delattr(book2down, 'end_chapter')
            
        if status == 'err':
            print('找不到此书')
            return 'err'
        else:
            return 's'
    except ValueError:
        return 'err'


class Config:
    def __init__(self):
        # 获取程序的基础路径
        if getattr(sys, 'frozen', False):
            # 如果是exe环境，使用exe所在目录
            self.script_dir = os.path.dirname(sys.executable)
        else:
            # 如果是Python环境，使用脚本所在目录
            self.script_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.data_dir = os.path.join(self.script_dir, 'data')
        self.bookstore_dir = os.path.join(self.data_dir, 'bookstore')
        self.config_path = os.path.join(self.data_dir, 'config.json')
        self.default_config = {
            'kg': 2,
            'kgf': '　',
            'delay': [50, 150],
            'save_path': '',
            'save_mode': 1,
            'space_mode': 'halfwidth',
            'xc': 1,
            'enable_chapter_numbering': False,
            'auto_retry': True,
            'max_retries': 3,
            'timeout': 10,
            'version': '1.1.16',
            'auto_backup': True
        }
        # 首次运行时直接使用默认配置
        if not os.path.exists(self.data_dir):
            self.config = self.default_config.copy()
        else:
            self.config = self.load_config()
            
    def create_directories(self):
        """创建必要的目录和文件"""
        try:
            # 创建data目录
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
                print(f"✓ 已创建数据目录: {self.data_dir}")
            
            # 创建bookstore目录
            if not os.path.exists(self.bookstore_dir):
                os.makedirs(self.bookstore_dir)
                print(f"✓ 已创建书库目录: {self.bookstore_dir}")
            
            # 创建或更新配置文件
            if not os.path.exists(self.config_path):
                with open(self.config_path, 'w', encoding='UTF-8') as f:
                    json.dump(self.default_config, f, indent=2, ensure_ascii=False)
                print(f"✓ 已创建配置文件: {self.config_path}")
            
            # 创建record.json
            record_path = os.path.join(self.data_dir, 'record.json')
            if not os.path.exists(record_path):
                with open(record_path, 'w', encoding='UTF-8') as f:
                    json.dump([], f)
                print(f"✓ 已创建下载记录文件: {record_path}")
                
            return True
        except Exception as e:
            print(f"创建目录或文件时出错: {e}")
            return False
            
    def __getitem__(self, key):
        try:
            return self.config[key]
        except (KeyError, TypeError):
            # 如果键不存在或config不是字典，返回默认配置中的值
            if isinstance(key, str) and key in self.default_config:
                return self.default_config[key]
            # 如果在默认配置中也不存在，返回None
            return None
        
    def __setitem__(self, key, value):
        self.config[key] = value
        self.save_config()
        
    def __contains__(self, key):
        return key in self.config or key in self.default_config

    def self_check(self):
        """执行程序自检"""
        check_results = {
            'runtime_env': {'status': True, 'details': []},
            'network': {'status': True, 'details': []},
            'files_and_dirs': {'status': True, 'details': []},
            'permissions': {'status': True, 'details': []},
            'config': {'status': True, 'details': []}
        }
        
        # 检查运行环境
        try:
            # 检查是否在 exe 环境中运行
            if getattr(sys, 'frozen', False):
                check_results['runtime_env']['details'].append("✓ 正在 exe 环境中运行")
                check_results['runtime_env']['details'].append(f"✓ 程序目录: {self.script_dir}")
            else:
                check_results['runtime_env']['details'].append("✓ 正在 Python 环境中运行")
            
            # 检查必要功能是否可用
            try:
                # 测试请求功能
                req.get('https://www.baidu.com', timeout=1)
                check_results['runtime_env']['details'].append("✓ 网络请求功能正常")
            except:
                pass
            
            try:
                # 测试文件操作功能
                test_file = os.path.join(self.data_dir, 'test.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                check_results['runtime_env']['details'].append("✓ 文件操作功能正常")
            except:
                check_results['runtime_env']['status'] = False
                check_results['runtime_env']['details'].append("✗ 文件操作功能异常")
            
            try:
                # 测试JSON功能
                json.dumps({"test": "test"})
                check_results['runtime_env']['details'].append("✓ JSON功能正常")
            except:
                check_results['runtime_env']['status'] = False
                check_results['runtime_env']['details'].append("✗ JSON功能异常")
                
        except Exception as e:
            check_results['runtime_env']['status'] = False
            check_results['runtime_env']['details'].append(f"✗ 运行环境检查出错: {str(e)}")
        
        # 检查网络连接
        try:
            response = req.get('https://fanqienovel.com', timeout=5)
            if response.status_code == 200:
                check_results['network']['details'].append("✓ 网站连接正常")
            else:
                check_results['network']['status'] = False
                check_results['network']['details'].append(f"✗ 网站返回状态码: {response.status_code}")
        except Exception as e:
            check_results['network']['status'] = False
            check_results['network']['details'].append(f"✗ 网络连接失败: {str(e)}")
        
        # 检查文件和目录
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            required_dirs = [self.data_dir, self.bookstore_dir]
            required_files = [self.config_path, os.path.join(self.data_dir, 'record.json')]
            
            for dir_path in required_dirs:
                if os.path.exists(dir_path):
                    if os.path.isdir(dir_path):
                        check_results['files_and_dirs']['details'].append(f"✓ 目录存在: {dir_path}")
                    else:
                        check_results['files_and_dirs']['status'] = False
                        check_results['files_and_dirs']['details'].append(f"✗ 路径不是目录: {dir_path}")
                else:
                    try:
                        os.makedirs(dir_path)
                        check_results['files_and_dirs']['details'].append(f"✓ 已创建目录: {dir_path}")
                    except:
                        check_results['files_and_dirs']['status'] = False
                        check_results['files_and_dirs']['details'].append(f"✗ 无法创建目录: {dir_path}")
                        
            for file_path in required_files:
                if os.path.exists(file_path):
                    check_results['files_and_dirs']['details'].append(f"✓ 文件存在: {file_path}")
                else:
                    check_results['files_and_dirs']['status'] = False
                    check_results['files_and_dirs']['details'].append(f"✗ 文件不存在: {file_path}")
                    
        except Exception as e:
            check_results['files_and_dirs']['status'] = False
            check_results['files_and_dirs']['details'].append(f"✗ 检查目录时出错: {str(e)}")
        
        # 检查文件权限
        try:
            files_to_check = [self.config_path]
            for file_path in files_to_check:
                if os.path.exists(file_path):
                    try:
                        # 检查读权限
                        with open(file_path, 'r', encoding='UTF-8') as f:
                            f.read(1)
                        check_results['permissions']['details'].append(f"✓ 文件可读: {file_path}")
                        
                        # 检查写权限
                        try:
                            with open(file_path, 'a', encoding='UTF-8') as f:
                                pass
                            check_results['permissions']['details'].append(f"✓ 文件可写: {file_path}")
                        except:
                            check_results['permissions']['status'] = False
                            check_results['permissions']['details'].append(f"✗ 文件不可写: {file_path}")
                    except:
                        check_results['permissions']['status'] = False
                        check_results['permissions']['details'].append(f"✗ 文件不可读: {file_path}")
                else:
                    try:
                        # 尝试创建文件
                        with open(file_path, 'w', encoding='UTF-8') as f:
                            json.dump(self.default_config, f, indent=2, ensure_ascii=False)
                        check_results['permissions']['details'].append(f"✓ 已创建配置文件: {file_path}")
                    except:
                        check_results['permissions']['status'] = False
                        check_results['permissions']['details'].append(f"✗ 无法创建文件: {file_path}")
        except Exception as e:
            check_results['permissions']['status'] = False
            check_results['permissions']['details'].append(f"✗ 检查文件权限时出错: {str(e)}")
        
        # 检查配置文件
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='UTF-8') as f:
                    config_data = json.load(f)
                    for key in self.default_config:
                        if key not in config_data:
                            check_results['config']['status'] = False
                            check_results['config']['details'].append(f"✗ 配置缺少字段: {key}")
                    if check_results['config']['status']:
                        check_results['config']['details'].append("✓ 配置文件完整")
            else:
                try:
                    # 尝试创建默认配置文件
                    with open(self.config_path, 'w', encoding='UTF-8') as f:
                        json.dump(self.default_config, f, indent=2, ensure_ascii=False)
                    check_results['config']['details'].append("✓ 已创建默认配置文件")
                except:
                    check_results['config']['status'] = False
                    check_results['config']['details'].append("✗ 无法创建配置文件")
        except Exception as e:
            check_results['config']['status'] = False
            check_results['config']['details'].append(f"✗ 检查配置文件时出错: {str(e)}")
        
        return check_results

    def load_config(self):
        try:
            # 首次运行时不尝试加载配置文件
            if not os.path.exists(self.data_dir):
                return self.default_config.copy()
                
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='UTF-8') as f:
                    try:
                        config = json.load(f)
                        # 合并默认配置和用户配置
                        merged_config = self.default_config.copy()
                        merged_config.update(config)
                        return merged_config
                    except json.JSONDecodeError:
                        print("配置文件格式错误，将使用默认配置")
                        # 备份错误的配置文件
                        if os.path.exists(self.config_path):
                            backup_path = self.config_path + '.backup'
                            try:
                                shutil.copy2(self.config_path, backup_path)
                                print(f"已备份原配置文件到: {backup_path}")
                            except Exception as e:
                                print(f"备份配置文件失败: {e}")
                        # 创建新的配置文件
                        with open(self.config_path, 'w', encoding='UTF-8') as f:
                            json.dump(self.default_config, f, indent=2, ensure_ascii=False)
                        return self.default_config.copy()
            return self.default_config.copy()
        except Exception as e:
            print(f"加载配置文件出错: {e}")
            return self.default_config.copy()
        
    def save_config(self):
        try:
            # 确保目录存在
            if os.path.exists(self.data_dir):
                with open(self.config_path, 'w', encoding='UTF-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件出错: {e}")
            
    def get(self, key, default=None):

        return self.config.get(key, default)
        
    def set(self, key, value):
        self.config[key] = value
        self.save_config()

# 初始化配置
config = Config()

def get_backup_path():
    if platform.system() == "Windows":
        backup_path = os.path.join(os.environ.get('APPDATA', ''), 'fanqie_downloader_backup')
    else:
        backup_path = os.path.join(os.path.expanduser('~'), '.fanqie_downloader_backup')
    return backup_path

def perform_backup():
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
            
        source_path = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(source_path, 'data')
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # 清理旧的备份
        if os.path.exists(backup_path):
            for item in os.listdir(backup_path):
                item_path = os.path.join(backup_path, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                except Exception as e:
                    print(f"清理旧备份文件失败: {e}")
                    

        data_backup_path = os.path.join(backup_path, 'data')
        if os.path.exists(data_dir):
            try:
                shutil.copytree(data_dir, data_backup_path)
                print("数据目录备份成功")
            except Exception as e:
                print(f"数据目录备份失败: {e}")
                return False
                
        print("\n备份完成！备份文件保存在:", backup_path)
        return True
    except Exception as e:
        print(f"备份过程出错: {e}")
        return False

def restore_backup():
    try:
        backup_path = get_backup_path()
        if not os.path.exists(backup_path):
            print("未找到备份文件")
            return False
            
        source_path = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(source_path, 'data')
        
        # 恢复data目录
        data_backup_path = os.path.join(backup_path, 'data')
        if os.path.exists(data_backup_path):
            # 如果目标目录存在，先删除
            if os.path.exists(data_dir):
                try:
                    shutil.rmtree(data_dir)
                except Exception as e:
                    print(f"删除旧数据目录失败: {e}")
                    return False
            
            try:
                shutil.copytree(data_backup_path, data_dir)
                print("✓ 数据目录恢复成功")
            except Exception as e:
                print(f"✗ 数据目录恢复失败: {e}")
                return False
        else:
            print("未找到数据目录备份")
            return False
            
        print("\n恢复完成！")
        return True
    except Exception as e:
        print(f"恢复过程出错: {e}")
        return False

# 初始化并运行配置检查器
config_checker = ConfigChecker()
config_check_result = config_checker.perform_check(config.config_path, config.config)

if config_check_result:
    config.create_directories()  # 创建必要的目录
else:
    print("\n警告：配置检查未完全通过，建议检查配置文件或重新生成配置文件。")
    choice = input("是否继续运行程序？(y/n): ")
    if choice.lower() != 'y':
        print("程序退出。")
        sys.exit(1)
    config.create_directories()  # 用户选择继续时也创建目录

# 使用Config实例中的路径
script_dir = config.script_dir
data_dir = config.data_dir
bookstore_dir = config.bookstore_dir
record_path = os.path.join(data_dir, 'record.json')
config_path = config.config_path

a = """
███████╗ █████╗ ███╗   ██╗ ██████╗ ██╗███████╗    ██████╗ ██╗     
██╔════╝██╔══██╗████╗  ██║██╔═══██╗██║██╔════╝    ██╔══██╗██║     
█████╗  ███████║██╔██╗ ██║██║   ██║██║█████╗      ██║  ██║██║     
██╔══╝  ██╔══██║██║╚██╗██║██║▄▄ ██║██║██╔══╝      ██║  ██║██║     
██║     ██║  ██║██║ ╚████║╚██████╔╝██║███████╗    ██████╔╝███████╗
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚══▀▀═╝ ╚═╝╚══════╝    ╚═════╝ ╚══════╝
"""

print(a)
print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & qxqycb')

# 检查备份
backup_path = get_backup_path()
if os.path.exists(backup_path) and config['auto_backup']:
    choice = input("检测到备份文件，是否恢复？1.恢复  2.跳过：")
    if choice == '1':
        if restore_backup():
            print("备份恢复成功！")
        else:
            print("备份恢复失败，将使用默认配置。")
    elif choice != '2':
        print("输入无效，跳过恢复")
elif not config['auto_backup']:
    print("自动备份功能已关闭")
else:
    print("未检测到备份文件")

# 初始化网络管理器并检测网络状态
print('\n正在检测网络状态...')
network_manager = NetworkManager()
network_manager.display_network_status()
if network_manager.check_network_status() < 30:
    print('警告：当前网络状况较差，可能会影响下载速度和稳定性')
elif network_manager.check_network_status() < 70:
    print('提示：当前网络状况一般，建议保持默认下载线程数')

# 获取cookie
print('正在获取cookie')
cookie_path = os.path.join(data_dir, 'cookie.json')
tzj = int(random.choice(list(down_zj(7143038691944959011)[1].values())[21:]))
cookie_loaded = False

if os.path.exists(cookie_path):
    try:
        with open(cookie_path, 'r', encoding='UTF-8') as f:
            cookie = json.load(f)
        if get_cookie(tzj, cookie) == 's':
            cookie_loaded = True
            print('成功')
    except Exception as e:
        print(f"加载cookie失败: {e}")

if not cookie_loaded:
    if get_cookie(tzj) == 's':
        print('成功')
    else:
        print('获取cookie失败，请检查网络连接')
        sys.exit(1)

async def text_to_speech(text, output_file, speaker='zh-CN-XiaoxiaoNeural'):
    try:
        communicate = edge_tts.Communicate(text, speaker)
        await communicate.save(output_file)
        return True
    except Exception as e:
        print(f"语音合成出错: {str(e)}")
        return False

async def process_segment(text, output_file):
    try:
        await text_to_speech(text, output_file)
        return True
    except Exception as e:
        print(f"语音合成出错: {str(e)}")
        return False

async def process_chapter(chapter_title, content, audio_dir):
    print(f"正在处理章节: {chapter_title}")
    try:
        # 将内容分段
        segments = content.split('\n')
        segments = [seg.strip() for seg in segments if seg.strip()]
        
        chapter_dir = os.path.join(audio_dir, sanitize_filename(chapter_title))
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)
        
        tasks = []
        for i, segment in enumerate(segments):
            output_file = os.path.join(chapter_dir, f"{i+1}.mp3")
            if not os.path.exists(output_file):
                tasks.append(process_segment(segment, output_file))
        
        if tasks:
            results = await asyncio.gather(*tasks)
            success = all(results)
        else:
            success = True
        
        if success:
            try:
                # 合并音频文件
                import pydub
                combined = pydub.AudioSegment.empty()
                for i in range(len(segments)):
                    mp3_file = os.path.join(chapter_dir, f"{i+1}.mp3")
                    if os.path.exists(mp3_file):
                        audio = pydub.AudioSegment.from_mp3(mp3_file)
                        combined += audio
                
                # 保存合并后的文件
                output_file = os.path.join(audio_dir, f"{sanitize_filename(chapter_title)}.mp3")
                combined.export(output_file, format="mp3")
                
                # 删除临时文件夹
                shutil.rmtree(chapter_dir)
                return True
            except Exception as e:
                print(f"合并音频文件时出错: {str(e)}")
                return False
    except Exception as e:
        print(f"处理章节 {chapter_title} 时出错: {str(e)}")
        return False
    return False

def export_audiobook(book_id, chapter_range=""):
    if not AUDIO_SUPPORT:
        print("未安装edge-tts,无法使用语音合成功能")
        print("请使用pip install edge-tts安装")
        return
    
    try:
        import pydub
    except ImportError:
        print("未安装pydub,无法使用音频处理功能")
        print("请使用pip install pydub安装")
        return
        
    try:
        name, chapters, zt = down_zj(book_id)
        if name == 'err':
            print("获取章节信息失败")
            return
            
        safe_name = sanitize_filename(name + chapter_range)
        audio_dir = os.path.join(script_dir, f"{safe_name}_audio")
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
            
        print(f"\n开始下载《{name}》的有声版本")
        
        async def process_all_chapters():
            tasks = []
            for chapter_title, chapter_id in chapters.items():
                content, _ = down_text(chapter_id)
                if content and content != 'err':
                    tasks.append(process_chapter(chapter_title, content, audio_dir))
                time.sleep(random.randint(config['delay'][0], config['delay'][1]) / 1000)
            
            if tasks:
                results = await asyncio.gather(*tasks)
                success_count = sum(1 for r in results if r)
                print(f"\n处理完成,成功转换{success_count}/{len(tasks)}章")
        
        try:
            asyncio.run(process_all_chapters())
        except KeyboardInterrupt:
            print("\n用户中断处理")
        except Exception as e:
            print(f"\n处理过程中出错: {str(e)}")
            
    except Exception as e:
        print(f"导出有声书时出错: {str(e)}")
        return

# 主循环
while True:
    print('\n输入书的id或链接直接下载\n输入下面的数字进入其他功能:')
    print('''
1. 更新小说
2. 搜索
3. 批量下载
4. 设置
5. 备份
6. 生成下载清单文件
7. 退出
8. 导出有声书
9. 程序自检
''')

    inp = input()

    if inp == '1':
        # 更新操作
        with open(record_path, 'r', encoding='UTF-8') as f:
            records = json.load(f)
        new_records = []
        for book_id in tqdm(records):
            status = book2down(book_id)
            if status != 'err' and status != '已完结':
                new_records.append(book_id)
        with open(record_path, 'w', encoding='UTF-8') as f:
            json.dump(new_records, f)
        print('更新完成')

    elif inp == '9':
        print("\n开始执行程序自检...")
        check_results = config.self_check()
        
        # 打印检查结果
        categories = {
            'runtime_env': '运行环境检查',
            'network': '网络连接检查',
            'files_and_dirs': '文件和目录检查',
            'permissions': '权限检查',
            'config': '配置文件检查'
        }
        
        all_passed = True
        for category, title in categories.items():
            result = check_results[category]
            status = "通过" if result['status'] else "失败"
            print(f"\n{title} - {status}")
            for detail in result['details']:
                print(f"  {detail}")
            if not result['status']:
                all_passed = False
        
        if all_passed:
            print("\n✓ 所有检查项目通过！程序运行环境正常。")
        else:
            print("\n✗ 检查发现问题，请查看上述详细信息并解决相关问题。")
            
        input("\n按Enter键继续...")

    elif inp == '8':
        book_id = input("请输入书籍ID或链接：")
        if str(book_id)[:4] == 'http':
            book_id = book_id.split('?')[0].split('/')[-1]
        try:
            book_id = int(book_id)
            export_audiobook(book_id)
        except ValueError:
            print("请输入有效的书籍ID")

    elif inp == '4':
        print('请选择项目：1.正文段首占位符 2.章节下载间隔延迟 3.小说保存路径 4.小说保存方式 5.设置下载线程数 6.章节排序 7.指定章节下载 8.自动备份设置')
        inp2 = input()
        if inp2 == '1':
            tmp = input('请输入正文段首占位符(当前为"%s")(直接Enter不更改)：' % config['kgf'])
            if tmp != '':
                config['kgf'] = tmp
            config['kg'] = int(input('请输入正文段首占位符数（当前为%d）：' % config['kg']))

        elif inp2 == '2':
            print('由于延迟过小造成的后果请自行负责。\n请输入下载间隔随机延迟的')
            config['delay'][0] = int(input('下限（当前为%d）（毫秒）：' % config['delay'][0]))
            config['delay'][1] = int(input('上限（当前为%d）（毫秒）：' % config['delay'][1]))

        elif inp2 == '3':
            print('tip:设置为当前目录点取消')
            time.sleep(1)
            config['save_path'] = select_save_directory()

        elif inp2 == '4':
            print('请选择：1.保存为单个 txt 2.分章保存 3.保存为 epub 4.保存为 HTML 网页格式 5.保存为 LaTeX')
            inp3 = input()
            if inp3 == '1':
                config['save_mode'] = 1
            elif inp3 == '2':
                config['save_mode'] = 2
            elif inp3 == '3':
                config['save_mode'] = 3
            elif inp3 == '4':
                config['save_mode'] = 4
            elif inp3 == '5':
                config['save_mode'] = 5
            else:
                print('请正确输入!')
                continue
        elif inp2 == '5':
            config['xc'] = int(input('请输入下载线程数：'))
        elif inp2 == '6':
            config['enable_chapter_numbering'] = input("是否开启章节排序功能？（1/2）：").lower() == '1'
        elif inp2 == '7':
            book_id = input("请输入书籍ID或链接：")
            try:
                if str(book_id)[:4] == 'http':
                    book_id = book_id.split('?')[0].split('/')[-1]
                book_id = int(book_id)
                
                # 获取章节信息
                name, chapters, zt = down_zj(book_id)
                if name == 'err':
                    print('找不到此书')
                    continue
                
                print(f"\n《{name}》共有 {len(chapters)} 章")
                start = input("请输入起始章节（直接回车从头开始）：")
                end = input("请输入结束章节（直接回车到最后）：")
                
                # 处理输入
                start = int(start) if start.strip() else 1
                end = int(end) if end.strip() else len(chapters)
                
                if start < 1:
                    start = 1
                if end > len(chapters):
                    end = len(chapters)
                if start > end:
                    print("起始章节不能大于结束章节！")
                    continue
                
                # 过滤章节并直接使用
                filtered_chapters = {}
                for i, (chapter_title, chapter_id) in enumerate(chapters.items(), 1):
                    if start <= i <= end:
                        filtered_chapters[chapter_title] = chapter_id
                
                # 保存章节范围信息到book2down函数
                book2down.start_chapter = start
                book2down.end_chapter = end
                
                print(f"\n开始下载第 {start} 章到第 {end} 章...")
                # 保存原始章节信息
                original_chapters = down_zj(book_id)[1]
                # 替换章节信息
                down_zj = lambda x: (name, filtered_chapters, zt)
                # 执行下载
                status = book2down(book_id)
                # 恢复原始函数
                down_zj = lambda x: (name, original_chapters, zt)
                
                if status == 'err':
                    print('下载失败')
                else:
                    print('下载完成')
                
            except ValueError:
                print("请输入有效的数字！")
                continue
        elif inp2 == '8':
            print(f"当前自动备份状态：{'开启' if config['auto_backup'] else '关闭'}")
            config['auto_backup'] = input("是否开启自动备份功能？（1.开启/2.关闭）：") == '1'
            if not config['auto_backup']:
                print("自动备份功能已关闭，您的设置和下载记录将不会自动备份")
            else:
                print("自动备份功能已开启，程序将自动备份您的设置和下载记录")
        else:
            print('请正确输入!')
            continue
        print('设置完成')

    elif inp == '2':
        tmp = search()
        if tmp == 'b':
            continue
        if book2down(tmp) == 'err':
            print('下载失败')

    elif inp == '3':
        urls_path = 'urls.txt'
        if not os.path.exists(urls_path):
            print(f"未到'{urls_path}'，将为您创建一个新的文件。")
            with open(urls_path, 'w', encoding='UTF-8') as file:
                file.write("# 请输入小说链接，一行一个\n")
        print(f"'{urls_path}' 已存在。请在文件中输入说链接，一行一个。")

        root = Tk()
        root.withdraw()
        root.update()
        if platform.system() == "Windows":
            os.startfile(urls_path)
        elif platform.system() == "Darwin":
            os.system(f"open -a TextEdit {urls_path}")
        else:
            os.system(f"xdg-open {urls_path}")
        print("输入完成后请保存并关闭文件，然后按 Enter 键继续...")
        input()
        try:
            with open(urls_path, 'r', encoding='UTF-8') as file:
                content = file.read()
                urls = content.replace(' ', '').split('\n')
            for url in urls:
                if url[0] != '#':
                    print(f'开始下载链接: {url}')
                    try:
                        status = book2down(url)
                        if status == 'err':
                            print(f'链接: {url} 下载失败。')
                        else:
                            print(f'链接: {url} 下载完成。')
                    except Exception as e:
                        print(f'处理链接 {url} 时出现错误：{e}')
        except Exception as e:
            print(f'读取 urls.txt 文件时出现错误：{e}')

    elif inp == '6':
        with open(record_path, 'r', encoding='UTF-8') as f:
            records = json.load(f)
        with open(os.path.join(script_dir, 'list.txt'), 'w', encoding='UTF-8') as list_file:
            for index, book_id in enumerate(records):
                name, zj, zt = down_zj(book_id)
                if name == 'err':
                    continue
                author_name = None
                url = f'https://fanqienovel.com/page/{book_id}'
                response = req.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                script_tag = soup.find('script', type="application/ld+json")
                if script_tag:
                    json_data = script_tag.string
                    data = json.loads(json_data)
                    if 'author' in data:
                        author_name = data['author'][0]['name']
                status = zt[0]
                chapter_count = len(zj)
                list_file.write(f'{index + 1}.{name}；作者：{author_name or "未知作者"}；{status}；共{chapter_count}章\n')

    elif inp == '5':
        perform_backup()
        print('备份完成')

    elif inp == '7':
        break

    else:
        if book2down(inp) == 'err':
            print('请输入有效的选项或书籍ID。')
