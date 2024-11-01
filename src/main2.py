# -*- coding: utf-8 -*-
import requests as req
from lxml import etree
from ebooklib import epub
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import time
import random
import os
import platform
import shutil
import concurrent.futures
from typing import Callable, Optional, Dict, List, Union
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
        charset_path = os.path.join(self.script_dir, 'charset.json')
        with open(charset_path, 'r', encoding='UTF-8') as f:
            self.charset = json.load(f)
        
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

    def _download_txt(self, novel_id: int) -> str:
        """Download novel in TXT format"""
        try:
            name, chapters, status = self._get_chapter_list(novel_id)
            if name == 'err':
                return 'err'

            safe_name = self._sanitize_filename(name)
            self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

            # Set book_json_path for the current download
            self.book_json_path = os.path.join(self.bookstore_dir, f'{safe_name}.json')
            
            # Initialize global variables for this download
            self.zj = {}
            self.cs = 0
            self.tcs = 0
            
            # Store metadata at the start
            metadata = {
                '_metadata': {
                    'novel_id': str(novel_id),  # Store as string to avoid JSON integer limits
                    'name': name,
                    'status': status[0] if status else None,
                    'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            # Load existing content and merge with metadata
            existing_content = {}
            if os.path.exists(self.book_json_path):
                with open(self.book_json_path, 'r', encoding='UTF-8') as f:
                    existing_content = json.load(f)
                    # Keep existing chapters but update metadata
                    if isinstance(existing_content, dict):
                        existing_content.update(metadata)
            else:
                existing_content = metadata
                # Save initial metadata
                with open(self.book_json_path, 'w', encoding='UTF-8') as f:
                    json.dump(existing_content, f, ensure_ascii=False)

            total_chapters = len(chapters)
            completed_chapters = 0

            # Create CLI progress bar
            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                # Download chapters
                content = existing_content.copy()  # Start with existing content including metadata
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            self._download_chapter, 
                            title, 
                            chapter_id, 
                            existing_content
                        ): title 
                        for title, chapter_id in chapters.items()
                    }

                    for future in concurrent.futures.as_completed(future_to_chapter):
                        chapter_title = future_to_chapter[future]
                        try:
                            chapter_content = future.result()
                            if chapter_content:
                                content[chapter_title] = chapter_content
                                # Save progress periodically
                                if completed_chapters % 5 == 0:
                                    with open(self.book_json_path, 'w', encoding='UTF-8') as f:
                                        json.dump(content, f, ensure_ascii=False)
                        except Exception as e:
                            self.log_callback(f'下载章节失败 {chapter_title}: {str(e)}')
                        
                        completed_chapters += 1
                        pbar.update(1)
                        self.progress_callback(
                            completed_chapters,
                            total_chapters,
                            '下载进度',
                            chapter_title
                        )

                # Save final content
                with open(self.book_json_path, 'w', encoding='UTF-8') as f:
                    json.dump(content, f, ensure_ascii=False)

                # Generate output file
                if self.config.save_mode == SaveMode.SINGLE_TXT:
                    return self._save_single_txt(safe_name, content)
                else:
                    return self._save_split_txt(safe_name, content)

        finally:
            # Send 100% completion if not already sent
            if 'completed_chapters' in locals() and 'total_chapters' in locals():
                if completed_chapters < total_chapters:
                    self.progress_callback(total_chapters, total_chapters, '下载完成')

    def _download_epub(self, novel_id: int) -> str:
        """Download novel in EPUB format"""
        try:
            name, chapters, status = self._get_chapter_list(novel_id)
            if name == 'err':
                return 'err'

            safe_name = self._sanitize_filename(name)
            self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

            # Create EPUB book
            book = epub.EpubBook()
            book.set_title(name)
            book.set_language('zh')

            # Get author info and cover
            author = self._get_author_info(novel_id)
            if author:
                book.add_author(author)
            cover_url = self._get_cover_url(novel_id)
            if cover_url:
                self._add_cover_to_epub(book, cover_url)

            total_chapters = len(chapters)
            completed_chapters = 0

            # Download chapters with progress tracking
            epub_chapters = []
            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            self._download_chapter_for_epub,
                            title,
                            chapter_id
                        ): title
                        for title, chapter_id in chapters.items()
                    }

                    for future in concurrent.futures.as_completed(future_to_chapter):
                        chapter_title = future_to_chapter[future]
                        try:
                            epub_chapter = future.result()
                            if epub_chapter:
                                epub_chapters.append(epub_chapter)
                                book.add_item(epub_chapter)
                        except Exception as e:
                            self.log_callback(f'下载章节失败 {chapter_title}: {str(e)}')
                        
                        completed_chapters += 1
                        pbar.update(1)
                        self.progress_callback(
                            completed_chapters,
                            total_chapters,
                            '下载进度',
                            chapter_title
                        )

            # Add navigation
            book.toc = epub_chapters
            book.spine = ['nav'] + epub_chapters
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Save EPUB file
            epub_path = os.path.join(self.config.save_path, f'{safe_name}.epub')
            epub.write_epub(epub_path, book)
            return 's'

        finally:
            if 'completed_chapters' in locals() and 'total_chapters' in locals():
                if completed_chapters < total_chapters:
                    self.progress_callback(total_chapters, total_chapters, '下载完成')

    def _download_chapter(self, title: str, chapter_id: str, existing_content: Dict) -> Optional[str]:
        """Download a single chapter with retries"""
        if title in existing_content:
            self.zj[title] = existing_content[title]  # Add this
            return existing_content[title]

        self.log_callback(f'下载章节: {title}')
        retries = 3
        last_error = None
        
        while retries > 0:
            try:
                content = self._download_chapter_content(chapter_id)
                if content == 'err':  # Add this check
                    raise Exception('Download failed')
                
                time.sleep(random.randint(
                    self.config.delay[0], 
                    self.config.delay[1]
                ) / 1000)
                
                # Handle cookie refresh
                if content == 'err':
                    self.tcs += 1
                    if self.tcs > 7:
                        self.tcs = 0
                        self._get_new_cookie(self.tzj)
                    continue  # Try again with new cookie
                
                # Save progress periodically
                self.cs += 1
                if self.cs >= 5:
                    self.cs = 0
                    self._save_progress(title, content)
                
                self.zj[title] = content  # Add this
                return content
                
            except Exception as e:
                last_error = e
                retries -= 1
                if retries == 0:
                    self.log_callback(f'下载失败 {title}: {str(e)}')
                    break
                time.sleep(1)
        
        if last_error:
            raise last_error
        return None

    def _download_chapter_for_epub(self, title: str, chapter_id: str) -> Optional[epub.EpubHtml]:
        """Download and format chapter for EPUB"""
        content = self._download_chapter(title, chapter_id, {})
        if not content:
            return None

        chapter = epub.EpubHtml(
            title=title,
            file_name=f'chapter_{chapter_id}.xhtml',
            lang='zh'
        )
        
        formatted_content = content.replace(
            '\n', 
            f'\n{self.config.kgf * self.config.kg}'
        )
        chapter.content = f'<h1>{title}</h1><p>{formatted_content}</p>'
        return chapter

    def _save_single_txt(self, name: str, content: dict) -> str:
        """Save all chapters to a single TXT file"""
        output_path = os.path.join(self.config.save_path, f'{name}.txt')
        fg = '\n' + self.config.kgf * self.config.kg

        with open(output_path, 'w', encoding='UTF-8') as f:
            for title, chapter_content in content.items():
                f.write(f'\n{title}{fg}')
                if self.config.kg == 0:
                    f.write(f'{chapter_content}\n')
                else:
                    # 将替换结果存储在一个变量中
                    modified_content = chapter_content.replace("\n", fg)
                    # 在 f-string 中使用这个变量
                    f.write(f'{modified_content}\n')

    def _save_split_txt(self, name: str, content: Dict) -> str:
        """Save each chapter to a separate TXT file"""
        output_dir = os.path.join(self.config.save_path, name)
        os.makedirs(output_dir, exist_ok=True)

        for title, chapter_content in content.items():
            chapter_path = os.path.join(
                output_dir,
                f'{self._sanitize_filename(title)}.txt'
            )
            if self.config.kg == 0:
                replacement_content = chapter_content
            else:
                replacement_content = chapter_content.replace("\n", self.config.kgf * self.config.kg)

            with open(chapter_path, 'w', encoding='UTF-8') as f:
                f.write(f'{replacement_content}\n')

        return 's'

    def update_all_novels(self):
        """Update all novels in records"""
        if not os.path.exists(self.record_path):
            self.log_callback("No novels to update")
            return

        with open(self.record_path, 'r', encoding='UTF-8') as f:
            novels = json.load(f)

        for novel_id in novels:
            self.log_callback(f"Updating novel {novel_id}")
            status = self.download_novel(novel_id)
            if not status:
                novels.remove(novel_id)

        with open(self.record_path, 'w', encoding='UTF-8') as f:
            json.dump(novels, f)

    def _download_html(self, novel_id: int) -> str:
        """Download novel in HTML format"""
        try:
            name, chapters, status = self._get_chapter_list(novel_id)
            if name == 'err':
                return 'err'

            safe_name = self._sanitize_filename(name)
            html_dir = os.path.join(self.config.save_path, f"{safe_name}(html)")
            os.makedirs(html_dir, exist_ok=True)

            self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

            # Create index.html
            toc_content = self._create_html_index(name, chapters)
            with open(os.path.join(html_dir, "index.html"), "w", encoding='UTF-8') as f:
                f.write(toc_content)

            total_chapters = len(chapters)
            completed_chapters = 0

            # Download chapters with progress tracking
            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            self._download_chapter_for_html,
                            title,
                            chapter_id,
                            html_dir,
                            list(chapters.keys())
                        ): title
                        for title, chapter_id in chapters.items()
                    }

                    for future in concurrent.futures.as_completed(future_to_chapter):
                        chapter_title = future_to_chapter[future]
                        try:
                            future.result()
                        except Exception as e:
                            self.log_callback(f'下载章节失败 {chapter_title}: {str(e)}')
                        
                        completed_chapters += 1
                        pbar.update(1)
                        self.progress_callback(
                            completed_chapters,
                            total_chapters,
                            '下载进度',
                            chapter_title
                        )

            return 's'

        finally:
            if 'completed_chapters' in locals() and 'total_chapters' in locals():
                if completed_chapters < total_chapters:
                    self.progress_callback(total_chapters, total_chapters, '下载完成')

    def _download_latex(self, novel_id: int) -> str:
        """Download novel in LaTeX format"""
        try:
            name, chapters, status = self._get_chapter_list(novel_id)
            if name == 'err':
                return 'err'

            safe_name = self._sanitize_filename(name)
            self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

            # Create LaTeX document header
            latex_content = self._create_latex_header(name)
            
            total_chapters = len(chapters)
            completed_chapters = 0
            chapter_contents = []

            # Download chapters with progress tracking
            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            self._download_chapter_for_latex,
                            title,
                            chapter_id
                        ): title
                        for title, chapter_id in chapters.items()
                    }

                    for future in concurrent.futures.as_completed(future_to_chapter):
                        chapter_title = future_to_chapter[future]
                        try:
                            chapter_content = future.result()
                            if chapter_content:
                                chapter_contents.append((chapter_title, chapter_content))
                        except Exception as e:
                            self.log_callback(f'下载章节失败 {chapter_title}: {str(e)}')
                        
                        completed_chapters += 1
                        pbar.update(1)
                        self.progress_callback(
                            completed_chapters,
                            total_chapters,
                            '下载进度',
                            chapter_title
                        )

            # Sort chapters and add to document
            chapter_contents.sort(key=lambda x: list(chapters.keys()).index(x[0]))
            for title, content in chapter_contents:
                latex_content += self._format_latex_chapter(title, content)

            # Add document footer and save
            latex_content += "\n\\end{document}"
            latex_path = os.path.join(self.config.save_path, f'{safe_name}.tex')
            with open(latex_path, 'w', encoding='UTF-8') as f:
                f.write(latex_content)

            return 's'

        finally:
            if 'completed_chapters' in locals() and 'total_chapters' in locals():
                if completed_chapters < total_chapters:
                    self.progress_callback(total_chapters, total_chapters, '下载完成')

    def _create_html_index(self, title: str, chapters: Dict[str, str]) -> str:
        """Create HTML index page with CSS styling"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 目录</title>
    <style>
        :root {{
            --bg-color: #f5f5f5;
            --text-color: #333;
            --link-color: #007bff;
            --hover-color: #0056b3;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #222;
                --text-color: #fff;
                --link-color: #66b0ff;
                --hover-color: #99ccff;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .toc {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }}
        .toc a {{
            color: var(--link-color);
            text-decoration: none;
            display: block;
            padding: 8px 0;
            transition: all 0.2s;
        }}
        .toc a:hover {{
            color: var(--hover-color);
            transform: translateX(10px);
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="toc">
        {''.join(f'<a href="{self._sanitize_filename(title)}.html">{title}</a>' for title in chapters.keys())}
    </div>
</body>
</html>
"""

    def _create_latex_header(self, title: str) -> str:
        """Create LaTeX document header"""
        return f"""\\documentclass[12pt,a4paper]{{article}}
\\usepackage{{ctex}}
\\usepackage{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{bookmark}}

\\geometry{{
    top=2.54cm,
    bottom=2.54cm,
    left=3.18cm,
    right=3.18cm
}}

\\title{{{title}}}
\\author{{Generated by NovelDownloader}}
\\date{{\\today}}

\\begin{{document}}
\\maketitle
\\tableofcontents
\\newpage
"""

    def _download_chapter_for_html(self, title: str, chapter_id: str, output_dir: str, all_titles: List[str]) -> None:
        """Download and format chapter for HTML"""
        content = self._download_chapter(title, chapter_id, {})
        if not content:
            return

        current_index = all_titles.index(title)
        prev_link = f'<a href="{self._sanitize_filename(all_titles[current_index-1])}.html">上一章</a>' if current_index > 0 else ''
        next_link = f'<a href="{self._sanitize_filename(all_titles[current_index+1])}.html">下一章</a>' if current_index < len(all_titles)-1 else ''

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* ... Same CSS variables as index ... */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
            max-width: 800px;
            margin: 0 auto;
        }}
        .navigation {{
            display: flex;
            justify-content: space-between;
            padding: 20px 0;
            position: sticky;
            top: 0;
            background-color: var(--bg-color);
        }}
        .navigation a {{
            color: var(--link-color);
            text-decoration: none;
            padding: 8px 16px;
            border: 1px solid var(--link-color);
            border-radius: 4px;
        }}
        .content {{
            text-indent: 2em;
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="navigation">
        <a href="index.html">目录</a>
        {prev_link}
        {next_link}
    </div>
    <h1>{title}</h1>
    <div class="content">
        {content.replace(chr(10), '<br>' + self.config.kgf * self.config.kg)}
    </div>
    <div class="navigation">
        <a href="index.html">目录</a>
        {prev_link}
        {next_link}
    </div>
</body>
</html>
"""
        
        with open(os.path.join(output_dir, f"{self._sanitize_filename(title)}.html"), "w", encoding='UTF-8') as f:
            f.write(html_content)

    def _download_chapter_for_latex(self, title: str, chapter_id: str) -> Optional[str]:
        """Download and format chapter for LaTeX"""
        content = self._download_chapter(title, chapter_id, {})
        if not content:
            return None
        return self._format_latex_chapter(title, content)

    def _format_latex_chapter(self, title: str, content: str) -> str:
        """Format chapter content for LaTeX"""
        # Escape special LaTeX characters
        special_chars = ['\\', '{', '}', '&', '#', '$', '^', '_', '~', '%']
        for char in special_chars:
            content = content.replace(char, f'\\{char}')
            title = title.replace(char, f'\\{char}')

        # Format content with proper spacing
        content = content.replace('\n', '\n\n' + self.config.kgf * self.config.kg)
        
        return f"""
\\section{{{title}}}
{content}
"""

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

    def _get_author_info(self, novel_id: int) -> Optional[str]:
        """Get author information from novel page"""
        url = f'https://fanqienovel.com/page/{novel_id}'
        try:
            response = req.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', type="application/ld+json")
            if script_tag:
                data = json.loads(script_tag.string)
                if 'author' in data:
                    return data['author'][0]['name']
        except Exception as e:
            self.log_callback(f"获取作者信息失败: {str(e)}")
        return None

    def _get_cover_url(self, novel_id: int) -> Optional[str]:
        """Get cover image URL from novel page"""
        url = f'https://fanqienovel.com/page/{novel_id}'
        try:
            response = req.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tag = soup.find('script', type="application/ld+json")
            if script_tag:
                data = json.loads(script_tag.string)
                if 'image' in data:
                    return data['image'][0]
        except Exception as e:
            self.log_callback(f"获取封面图片失败: {str(e)}")
        return None

    def _add_cover_to_epub(self, book: epub.EpubBook, cover_url: str):
        """Add cover image to EPUB book"""
        try:
            response = req.get(cover_url)
            if response.status_code == 200:
                book.set_cover('cover.jpg', response.content)
                
                # Add cover page
                cover_content = f'''
                    <div style="text-align: center; padding: 0; margin: 0;">
                        <img src="cover.jpg" alt="Cover" style="max-width: 100%; height: auto;"/>
                    </div>
                '''
                cover_page = epub.EpubHtml(
                    title='Cover',
                    file_name='cover.xhtml',
                    content=cover_content,
                    media_type='image/jpeg'
                )
                book.add_item(cover_page)
                book.spine.insert(0, cover_page)
        except Exception as e:
            self.log_callback(f"添加封面失败: {str(e)}")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for different platforms"""
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        illegal_chars_rep = ['＜', '＞', '：', '＂', '／', '＼', '｜', '？', '＊']
        for old, new in zip(illegal_chars, illegal_chars_rep):
            filename = filename.replace(old, new)
        return filename

    def _parse_novel_id(self, novel_id: Union[str, int]) -> Optional[int]:
        """Parse novel ID from input (URL or ID)"""
        if isinstance(novel_id, str) and novel_id.startswith('http'):
            novel_id = novel_id.split('?')[0].split('/')[-1]
        try:
            return int(novel_id)
        except ValueError:
            self.log_callback(f'Invalid novel ID: {novel_id}')
            return None

    def get_downloaded_novels(self) -> List[Dict[str, str]]:
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

    def backup_data(self, backup_dir: str):
        """Backup all data to specified directory"""
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup configuration
        if os.path.exists(self.config_path):
            shutil.copy2(self.config_path, os.path.join(backup_dir, 'config.json'))
            
        # Backup records
        if os.path.exists(self.record_path):
            shutil.copy2(self.record_path, os.path.join(backup_dir, 'record.json'))
            
        # Backup novels
        novels_backup_dir = os.path.join(backup_dir, 'novels')
        os.makedirs(novels_backup_dir, exist_ok=True)
        for novel in self.get_downloaded_novels():
            shutil.copy2(novel['json_path'], novels_backup_dir)

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

    def _update_records(self, novel_id: int):
        """Update download records"""
        if os.path.exists(self.record_path):
            with open(self.record_path, 'r', encoding='UTF-8') as f:
                records = json.load(f)
        else:
            records = []
            
        if novel_id not in records:
            records.append(novel_id)
            with open(self.record_path, 'w', encoding='UTF-8') as f:
                json.dump(records, f)

    def _save_progress(self, title: str, content: str):
        """Save download progress"""
        self.zj[title] = content
        with open(self.book_json_path, 'w', encoding='UTF-8') as f:
            json.dump(self.zj, f, ensure_ascii=False)

def create_cli():
    """Create CLI interface using the NovelDownloader class"""
    print('本程序完全免费。\nGithub: https://github.com/ying-ck/fanqienovel-downloader\n作者：Yck & qxqycb')
    
    config = Config()
    downloader = NovelDownloader(config)
    
    # Check for backup
    backup_folder_path = 'C:\\Users\\Administrator\\fanqie_down_backup'
    if os.path.exists(backup_folder_path):
        choice = input("检测到备份文件夹，是否使用备份数据？1.使用备份  2.跳过：")
        if choice == '1':
            if os.path.isdir(backup_folder_path):
                source_folder_path = os.path.dirname(os.path.abspath(__file__))
                for item in os.listdir(backup_folder_path):
                    source_item_path = os.path.join(backup_folder_path, item)
                    target_item_path = os.path.join(source_folder_path, item)
                    if os.path.isfile(source_item_path):
                        if os.path.exists(target_item_path):
                            os.remove(target_item_path)
                        shutil.copy2(source_item_path, target_item_path)
                    elif os.path.isdir(source_item_path):
                        if os.path.exists(target_item_path):
                            shutil.rmtree(target_item_path)
                        shutil.copytree(source_item_path, target_item_path)
            else:
                print("备份文件夹不存在，无法使用备份数据。")
        elif choice != '2':
            print("入无效，请重新运行程序并正确输入。")
    else:
        print("程序还未备份")

    while True:
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
            downloader.update_all_novels()
            
        elif inp == '2':
            while True:
                key = input("请输入搜索关键词（直接Enter返回）：")
                if key == '':
                    break
                results = downloader.search_novel(key)
                if not results:
                    print("没有找到相关书籍。")
                    continue
                    
                for i, book in enumerate(results):
                    print(f"{i + 1}. 名称：{book['book_data'][0]['book_name']} "
                          f"作者：{book['book_data'][0]['author']} "
                          f"ID：{book['book_data'][0]['book_id']} "
                          f"字数：{book['book_data'][0]['word_number']}")
                
                while True:
                    choice = input("请选择一个结果, 输入 r 以重新搜索：")
                    if choice == "r":
                        break
                    elif choice.isdigit() and 1 <= int(choice) <= len(results):
                        chosen_book = results[int(choice) - 1]
                        downloader.download_novel(chosen_book['book_data'][0]['book_id'])
                        break
                    else:
                        print("输入无效，请重新输入。")
                        
        elif inp == '3':
            urls_path = 'urls.txt'
            if not os.path.exists(urls_path):
                print(f"未找到'{urls_path}'，将为您创建一个新的文件。")
                with open(urls_path, 'w', encoding='UTF-8') as file:
                    file.write("# 请输入小说链接，一行一个\n")
            
            print(f"\n请在文本编辑器中打开并编辑 '{urls_path}'")
            print("在文件中输入小说链接，一行一个")
            
            if platform.system() == "Windows":
                os.system(f'notepad "{urls_path}"')
            elif platform.system() == "Darwin":
                os.system(f'open -e "{urls_path}"')
            else:
                if os.system('which nano > /dev/null') == 0:
                    os.system(f'nano "{urls_path}"')
                elif os.system('which vim > /dev/null') == 0:
                    os.system(f'vim "{urls_path}"')
                else:
                    print(f"请使用任意文本编辑器手动编辑 {urls_path} 文件")
            
            print("\n编辑完成后按Enter键继续...")
            input()
            
            with open(urls_path, 'r', encoding='UTF-8') as file:
                content = file.read()
                urls = content.replace(' ', '').split('\n')
            
            for url in urls:
                if url and url[0] != '#':
                    print(f'开始下载链接: {url}')
                    status = downloader.download_novel(url)
                    if not status:
                        print(f'链接: {url} 下载失败。')
                    else:
                        print(f'链接: {url} 下载完成。')
                        
        elif inp == '4':
            print('请选择项目：1.正文段首占位符 2.章节下载间隔延迟 3.小说保存路径 4.小说保存方式 5.设置下载线程数')
            inp2 = input()
            if inp2 == '1':
                tmp = input('请输入正文段首占位符(当前为"%s")(直接Enter不更改)：' % config.kgf)
                if tmp != '':
                    config.kgf = tmp
                config.kg = int(input('请输入正文段首占位符数（当前为%d）：' % config.kg))
            elif inp2 == '2':
                print('由于迟过小造成的后果请自行负责。\n请输入下载间隔随机延迟')
                config.delay[0] = int(input('下限（当前为%d）（毫秒）：' % config.delay[0]))
                config.delay[1] = int(input('上限（当前为%d）（毫秒）：' % config.delay[1]))
            elif inp2 == '3':
                print('tip:设置为当前目录点取消')
                time.sleep(1)
                path = input("\n请输入保存目录的完整路径:\n(直接按Enter使用当前目录)\n").strip()
                if path == "":
                    config.save_path = os.getcwd()
                else:
                    if not os.path.exists(path):
                        try:
                            os.makedirs(path)
                            config.save_path = path
                        except:
                            print("无法创建目录，将使用当前目录")
                            config.save_path = os.getcwd()
                    else:
                        config.save_path = path
            elif inp2 == '4':
                print('请选择：1.保存为单个 txt 2.分章保存 3.保存为 epub 4.保存为 HTML 网页格式 5.保存为 LaTeX')
                inp3 = input()
                try:
                    config.save_mode = SaveMode(int(inp3))
                except ValueError:
                    print('请正确输入!')
                    continue
            elif inp2 == '5':
                config.xc = int(input('请输入下载线程数：'))
            else:
                print('请正确输入!')
                continue
            
            # Save config
            with open(downloader.config_path, 'w', encoding='UTF-8') as f:
                json.dump({
                    'kg': config.kg,
                    'kgf': config.kgf,
                    'delay': config.delay,
                    'save_path': config.save_path,
                    'save_mode': config.save_mode.value,
                    'space_mode': config.space_mode,
                    'xc': config.xc
                }, f)
            print('设置完成')
            
        elif inp == '5':
            downloader.backup_data('C:\\Users\\Administrator\\fanqie_down_backup')
            print('备份完成')
            
        elif inp == '6':
            break
            
        else:
            # Try to download novel directly
            if downloader.download_novel(inp):
                print('下载完成')
            else:
                print('请输入有效的选项或书籍ID。')

if __name__ == "__main__":
    create_cli()

