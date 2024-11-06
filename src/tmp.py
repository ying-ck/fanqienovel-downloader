# -*- coding: utf-8 -*-
import requests as req
from lxml import etree
from tqdm import tqdm
import json, time, random, os
from typing import Callable, Optional
from dataclasses import dataclass

import src.down.txt
import utils, cookie, down
from settings import Config, SaveMode


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
        charset_path = os.path.join(self.script_dir, 'charset.json')
        with open(charset_path, 'r', encoding='UTF-8') as f:
            self.charset = json.load(f)

        self._setup_directories()
        self.cookie=""
        cookie.init(self)

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
        return self.DownloadProgress(
            current=current,
            total=total,
            percentage=(current / total * 100) if total > 0 else 0,
            description=desc,
            chapter_title=chapter_title
        )

    def download_novel(self, novel_id: str) -> bool:
        """
        Download a novel by its ID
        Returns True if successful, False otherwise
        """
        try:
            novel_id = utils.parse_novel_id(self, novel_id)
            if not novel_id:
                return False

            utils.update_records(self.record_path, novel_id)

            if self.config.save_mode == SaveMode.EPUB:
                status = down.epub(self, novel_id)
            elif self.config.save_mode == SaveMode.HTML:
                status = down.html(self, novel_id)
            elif self.config.save_mode == SaveMode.LATEX:
                status = down.latex(self, novel_id)
            else:
                status = down.txt(self, novel_id)

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

    def search_novel(self, keyword: str) -> list[dict]:
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
                    return utils.decode_content(self, content)
                except:
                    # Try alternative decoding mode
                    try:
                        return utils.decode_content(self, content, mode=1)
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

                    return utils.decode_content(self, content)
                except:
                    if attempt == 2:  # Last attempt
                        if test_mode:
                            return 'err'
                        raise Exception(f"Download failed after 3 attempts: {str(e)}")
                    time.sleep(1)

    def get_downloaded_novels(self) -> list[dict[str, str]]:
        """Get list of downloaded novels with their paths"""
        novels = []
        for filename in os.listdir(self.bookstore_dir):
            if filename.endswith('.json'):
                novel_name = filename[:-5]  # Remove .json extension
                json_path = os.path.join(self.bookstore_dir, filename)

                try:
                    with open(json_path, 'r', encoding='UTF-8') as f:
                        novel_data = json.load(f)
                        metadata = novel_data.get('_metadata', {})

                        novels.append({
                            'name': novel_name,
                            'novel_id': metadata.get('novel_id'),
                            'status': metadata.get('status'),
                            'last_updated': metadata.get('last_updated'),
                            'json_path': json_path,
                            'txt_path': os.path.join(self.config.save_path, f'{novel_name}.txt'),
                            'epub_path': os.path.join(self.config.save_path, f'{novel_name}.epub'),
                            'html_path': os.path.join(self.config.save_path, f'{novel_name}(html)'),
                            'latex_path': os.path.join(self.config.save_path, f'{novel_name}.tex')
                        })
                except Exception as e:
                    self.log_callback(f"Error reading novel data for {novel_name}: {str(e)}")
                    # Add novel with minimal info if metadata can't be read
                    novels.append({
                        'name': novel_name,
                        'novel_id': None,
                        'status': None,
                        'last_updated': None,
                        'json_path': json_path,
                        'txt_path': os.path.join(self.config.save_path, f'{novel_name}.txt'),
                        'epub_path': os.path.join(self.config.save_path, f'{novel_name}.epub'),
                        'html_path': os.path.join(self.config.save_path, f'{novel_name}(html)'),
                        'latex_path': os.path.join(self.config.save_path, f'{novel_name}.tex')
                    })
        return novels

