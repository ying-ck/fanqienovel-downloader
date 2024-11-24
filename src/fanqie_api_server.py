# -*- coding: utf-8 -*-
import requests as req
from lxml import etree
import threading  # Add this line
# from ebooklib import epub
# from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import time
import random
import os
import platform
import concurrent.futures
from typing import Callable, Optional, Dict, List, Union
from dataclasses import dataclass
from enum import Enum
from flask import Flask, jsonify, request

app = Flask(__name__)
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
    delay: List[int] = None
    save_path: str = ''
    save_mode: SaveMode = SaveMode.SINGLE_TXT
    space_mode: str = 'halfwidth'
    xc: int = 1

    def __post_init__(self):
        if self.delay is None:
            self.delay = [50, 150]

class NovelDownloader:
    def __init__(self, 
                 config: Config,
                 progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        self.config = config
        self.progress_callback = progress_callback or self._default_progress
        self.log_callback = log_callback or print
        
        # Initialize headers first
        self.headers_lib = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.47'}
        ]
        self.headers = random.choice(self.headers_lib)
        
        # Use absolute paths based on script location
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.script_dir, 'data')
        self.bookstore_dir = os.path.join(self.data_dir, 'bookstore')
        self.record_path = os.path.join(self.data_dir, 'record.json')
        self.config_path = os.path.join(self.data_dir, 'config.json')
        self.cookie_path = os.path.join(self.data_dir, 'cookie.json')
        
        self.CODE = [[58344, 58715], [58345, 58716]]
        
        # Load charset for text decoding
        self.charset = [["D","在","主","特","家","军","然","表","场","4","要","只","v","和","?","6","别","还","g","现","儿","岁","?","?","此","象","月","3","出","战","工","相","o","男","直","失","世","F","都","平","文","什","V","O","将","真","T","那","当","?","会","立","些","u","是","十","张","学","气","大","爱","两","命","全","后","东","性","通","被","1","它","乐","接","而","感","车","山","公","了","常","以","何","可","话","先","p","i","叫","轻","M","士","w","着","变","尔","快","l","个","说","少","色","里","安","花","远","7","难","师","放","t","报","认","面","道","S","?","克","地","度","I","好","机","U","民","写","把","万","同","水","新","没","书","电","吃","像","斯","5","为","y","白","几","日","教","看","但","第","加","候","作","上","拉","住","有","法","r","事","应","位","利","你","声","身","国","问","马","女","他","Y","比","父","x","A","H","N","s","X","边","美","对","所","金","活","回","意","到","z","从","j","知","又","内","因","点","Q","三","定","8","R","b","正","或","夫","向","德","听","更","?","得","告","并","本","q","过","记","L","让","打","f","人","就","者","去","原","满","体","做","经","K","走","如","孩","c","G","给","使","物","?","最","笑","部","?","员","等","受","k","行","一","条","果","动","光","门","头","见","往","自","解","成","处","天","能","于","名","其","发","总","母","的","死","手","入","路","进","心","来","h","时","力","多","开","已","许","d","至","由","很","界","n","小","与","Z","想","代","么","分","生","口","再","妈","望","次","西","风","种","带","J","?","实","情","才","这","?","E","我","神","格","长","觉","间","年","眼","无","不","亲","关","结","0","友","信","下","却","重","己","老","2","音","字","m","呢","明","之","前","高","P","B","目","太","e","9","起","稜","她","也","W","用","方","子","英","每","理","便","四","数","期","中","C","外","样","a","海","们","任"],["s","?","作","口","在","他","能","并","B","士","4","U","克","才","正","们","字","声","高","全","尔","活","者","动","其","主","报","多","望","放","h","w","次","年","?","中","3","特","于","十","入","要","男","同","G","面","分","方","K","什","再","教","本","己","结","1","等","世","N","?","说","g","u","期","Z","外","美","M","行","给","9","文","将","两","许","张","友","0","英","应","向","像","此","白","安","少","何","打","气","常","定","间","花","见","孩","它","直","风","数","使","道","第","水","已","女","山","解","d","P","的","通","关","性","叫","儿","L","妈","问","回","神","来","S","","四","望","前","国","些","O","v","l","A","心","平","自","无","军","光","代","是","好","却","c","得","种","就","意","先","立","z","子","过","Y","j","表","","么","所","接","了","名","金","受","J","满","眼","没","部","那","m","每","车","度","可","R","斯","经","现","门","明","V","如","走","命","y","6","E","战","很","上","f","月","西","7","长","夫","想","话","变","海","机","x","到","W","一","成","生","信","笑","但","父","开","内","东","马","日","小","而","后","带","以","三","几","为","认","X","死","员","目","位","之","学","远","人","音","呢","我","q","乐","象","重","对","个","被","别","F","也","书","稜","D","写","还","因","家","发","时","i","或","住","德","当","o","l","比","觉","然","吃","去","公","a","老","亲","情","体","太","b","万","C","电","理","?","失","力","更","拉","物","着","原","她","工","实","色","感","记","看","出","相","路","大","你","候","2","和","?","与","p","样","新","只","便","最","不","进","T","r","做","格","母","总","爱","身","师","轻","知","往","加","从","?","天","e","H","?","听","场","由","快","边","让","把","任","8","条","头","事","至","起","点","真","手","这","难","都","界","用","法","n","处","下","又","Q","告","地","5","k","t","岁","有","会","果","利","民"]]
        
        self._setup_directories()
        self._init_cookie()
        
        # Add these variables
        self.zj = {}  # For storing chapter data
        self.cs = 0   # Chapter counter
        self.tcs = 0  # Test counter
        self.tzj = None  # Test chapter ID
        self.book_json_path = None  # Current book's JSON path

    def _setup_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.bookstore_dir, exist_ok=True)

    def _init_cookie(self):
        """Initialize cookie for downloads"""
        self.log_callback('正在获取cookie')
        tzj = self._get_initial_chapter_id()
        
        if os.path.exists(self.cookie_path):
            with open(self.cookie_path, 'r', encoding='UTF-8') as f:
                self.cookie = json.load(f)
                if self._test_cookie(tzj, self.cookie) == 'err':
                    self._get_new_cookie(tzj)
        else:
            self._get_new_cookie(tzj)
        
        self.log_callback('Cookie获取成功')

    @dataclass
    class DownloadProgress:
        """Progress info for both CLI and web"""
        current: int
        total: int
        percentage: float
        description: str
        chapter_title: Optional[str] = None
        status: str = 'downloading'  # 'downloading', 'completed', 'error'
        error: Optional[str] = None

    def _default_progress(self, current: int, total: int, desc: str = '', chapter_title: str = None) -> DownloadProgress:
        """Progress tracking for both CLI and web"""
        # For CLI: Use tqdm directly
        if not hasattr(self, '_pbar'):
            self._pbar = tqdm(total=total, desc=desc)
        self._pbar.update(1)  # Update by 1 instead of setting n directly
        
        # For web: Return progress info
        return DownloadProgress(
            current=current,
            total=total,
            percentage=(current / total * 100) if total > 0 else 0,
            description=desc,
            chapter_title=chapter_title
        )

    def download_novel(self, novel_id: Union[str, int]) -> bool:
        """
        Download a novel by its ID
        Returns True if successful, False otherwise
        """
        try:
            novel_id = self._parse_novel_id(novel_id)
            if not novel_id:
                return False
                
            self._update_records(novel_id)
            
            if self.config.save_mode == SaveMode.EPUB:
                status = self._download_epub(novel_id)
            elif self.config.save_mode == SaveMode.HTML:
                status = self._download_html(novel_id)
            elif self.config.save_mode == SaveMode.LATEX:
                status = self._download_latex(novel_id)
            else:
                status = self._download_txt(novel_id)
                
            if status == 'err':
                self.log_callback('找不到此书')
                return False
            elif status == '已完结':
                self.log_callback('小说已完结')
                return True
            else:
                self.log_callback('下载完成')
                return True
            
        except Exception as e:
            self.log_callback(f'下载失败: {str(e)}')
            return False

    def search_novel(self, keyword: str) -> List[Dict]:
        """
        Search for novels by keyword
        Returns list of novel info dictionaries
        """
        if not keyword:
            return []
            
        # Use the correct API endpoint from ref_main.py
        url = f"https://api5-normal-lf.fqnovel.com/reading/bookapi/search/page/v/"
        params = {
            "query": keyword,
            "aid": "1967",
            "channel": "0",
            "os_version": "0",
            "device_type": "0",
            "device_platform": "0",
            "iid": "466614321180296",
            "passback": "{(page-1)*10}",
            "version_code": "999"
        }
        
        try:
            response = req.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data['code'] == 0 and data['data']:
                return data['data']
            else:
                self.log_callback("没有找到相关书籍。")
                return []
            
        except req.RequestException as e:
            self.log_callback(f"网络请求失败: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.log_callback(f"解析搜索结果失败: {str(e)}")
            return []
        except Exception as e:
            self.log_callback(f'搜索失败: {str(e)}')
            return []

    # ... Additional helper methods would go here ...

    def _get_initial_chapter_id(self) -> int:
        """Get an initial chapter ID for cookie testing"""
        test_novel_id = 7143038691944959011  # Example novel ID
        chapters = self._get_chapter_list(test_novel_id)
        if chapters and len(chapters[1]) > 21:
            return int(random.choice(list(chapters[1].values())[21:]))
        raise Exception("Failed to get initial chapter ID")

    def _get_new_cookie(self, chapter_id: int):
        """Generate new cookie"""
        bas = 1000000000000000000
        for i in range(random.randint(bas * 6, bas * 8), bas * 9):
            time.sleep(random.randint(50, 150) / 1000)
            self.cookie = f'novel_web_id={i}'
            if len(self._download_chapter_content(chapter_id, test_mode=True)) > 200:
                with open(self.cookie_path, 'w', encoding='UTF-8') as f:
                    json.dump(self.cookie, f)
                return

    def _test_cookie(self, chapter_id: int, cookie: str) -> str:
        """Test if cookie is valid"""
        self.cookie = cookie
        if len(self._download_chapter_content(chapter_id, test_mode=True)) > 200:
            return 's'
        return 'err'

    def _get_chapter_list(self, novel_id: int) -> tuple:
        """Get novel info and chapter list"""
        url = f'https://fanqienovel.com/page/{novel_id}'
        response = req.get(url, headers=self.headers)
        ele = etree.HTML(response.text)
        
        chapters = {}
        a_elements = ele.xpath('//div[@class="chapter"]/div/a')
        if not a_elements:  # Add this check
            return 'err', {}, []
            
        for a in a_elements:
            href = a.xpath('@href')
            if not href:  # Add this check
                continue
            chapters[a.text] = href[0].split('/')[-1]
            
        title = ele.xpath('//h1/text()')
        status = ele.xpath('//span[@class="info-label-yellow"]/text()')
        
        if not title or not status:  # Check both title and status
            return 'err', {}, []
            
        return title[0], chapters, status

    def _download_chapter_content(self, chapter_id: int, test_mode: bool = False) -> str:
        """Download content with fallback and better error handling"""
        headers = self.headers.copy()
        headers['cookie'] = self.cookie
        
        for attempt in range(3):
            try:
                # Try primary method
                response = req.get(
                    f'https://fanqienovel.com/reader/{chapter_id}', 
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                content = '\n'.join(
                    etree.HTML(response.text).xpath(
                        '//div[@class="muye-reader-content noselect"]//p/text()'
                    )
                )
                
                if test_mode:
                    return content
                    
                try:
                    return self._decode_content(content)
                except:
                    # Try alternative decoding mode
                    try:
                        return self._decode_content(content, mode=1)
                    except:
                        # Fallback HTML processing
                        content = content[6:]
                        tmp = 1
                        result = ''
                        for i in content:
                            if i == '<':
                                tmp += 1
                            elif i == '>':
                                tmp -= 1
                            elif tmp == 0:
                                result += i
                            elif tmp == 1 and i == 'p':
                                result = (result + '\n').replace('\n\n', '\n')
                        return result
                
            except Exception as e:
                # Try alternative API endpoint
                try:
                    response = req.get(
                        f'https://fanqienovel.com/api/reader/full?itemId={chapter_id}', 
                        headers=headers
                    )
                    content = json.loads(response.text)['data']['chapterData']['content']
                    
                    if test_mode:
                        return content
                        
                    return self._decode_content(content)
                except:
                    if attempt == 2:  # Last attempt
                        if test_mode:
                            return 'err'
                        raise Exception(f"Download failed after 3 attempts: {str(e)}")
                    time.sleep(1)

    def _decode_content(self, content: str, mode: int = 0) -> str:
        """Decode novel content using both charset modes"""
        result = ''
        for char in content:
            uni = ord(char)
            if self.CODE[mode][0] <= uni <= self.CODE[mode][1]:
                bias = uni - self.CODE[mode][0]
                if 0 <= bias < len(self.charset[mode]) and self.charset[mode][bias] != '?':
                    result += self.charset[mode][bias]
                else:
                    result += char
            else:
                result += char
        return result



config = Config()
downloader = NovelDownloader(config)

# Background thread function
def scheduled_cookie_update(interval: int):
    """Run _init_cookie at regular intervals"""
    while True:
        downloader._init_cookie()
        time.sleep(interval)

# 每日更新cookie  24小时*60*60=86400 
cookie_update_thread = threading.Thread(target=scheduled_cookie_update, args=(86400,))
cookie_update_thread.daemon = True  # Daemonize thread to exit with the main program
cookie_update_thread.start()

# 可以修改下面的路径/download_chapter_content
# api使用方式http://YOUR_ADDRESS:4888/download_chapter_content?chapter_id=${extractedId}
@app.route('/download_chapter_content', methods=['GET'])
def download_chapter_content():
    chapter_id = request.args.get('chapter_id', type=int)
    if not chapter_id:
        return jsonify({"error": "Missing chapter_id parameter"}), 400

    content = downloader._download_chapter_content(chapter_id)
    return jsonify({"content": content})
#修改端口号 默认4888
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0",port=4888)