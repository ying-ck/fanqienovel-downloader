# -*- coding: utf-8 -*-
import requests as req
from tqdm import tqdm
import json, os
from typing import Callable, Optional
from dataclasses import dataclass

import utils, cookie, down
from settings import Config, SaveMode
import settings


class NovelDownloader:
    def __init__(self,
                 config: Config,
                 progress_callback: Optional[Callable] = None,
                 log_callback: Optional[Callable] = None):
        self.config = config
        self.progress_callback = progress_callback or self._default_progress
        self.log_callback = log_callback or print

        os.makedirs(settings.data_dir, exist_ok=True)
        os.makedirs(settings.bookstore_dir, exist_ok=True)
        self.cookie=""
        cookie.init(self)

        # Add these variables
        self.zj = {}  # For storing chapter data
        self.cs = 0   # Chapter counter
        self.tcs = 0  # Test counter
        self.tzj = None  # Test chapter ID
        self.book_json_path = None  # Current book's JSON path

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

            utils.update_records(settings.record_path, novel_id)

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
            response = req.get(url, params=params, headers=settings.headers)
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

    def get_downloaded_novels(self) -> list[dict[str, str]]:
        """Get list of downloaded novels with their paths"""
        novels = []
        for filename in os.listdir(settings.bookstore_dir):
            if filename.endswith('.json'):
                novel_name = filename[:-5]  # Remove .json extension
                json_path = os.path.join(settings.bookstore_dir, filename)

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

