import time, json, os, random
import concurrent.futures
from tqdm import tqdm
from  ebooklib import epub

from src.settings import SaveMode
from src import format, utils, cookie

def txt(self, novel_id: int) -> str:
    """Download novel in TXT format"""
    try:
        name, chapters, status = self._get_chapter_list(novel_id)
        if name == 'err':
            return 'err'

        safe_name = utils.sanitize_filename(name)
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

def depub(self, novel_id: int) -> str:
    """Download novel in EPUB format"""
    try:
        name, chapters, status = self._get_chapter_list(novel_id)
        if name == 'err':
            return 'err'

        safe_name = utils.sanitize_filename(name)
        self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

        # Create EPUB book
        book = epub.EpubBook()
        book.set_title(name)
        book.set_language('zh')

        # Get author info and cover
        if author:= utils.get_author_info(self, novel_id):
            book.add_author(author)
        if cover_url:= format.epub.get_cover_url(self, novel_id):
            format.epub.add_cover(self, book, cover_url)

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

def _download_chapter(self, title: str, chapter_id: str, existing_content: dict) -> str | None:
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
                    cookie.get(self,self.tzj)
                continue  # Try again with new cookie

            # Save progress periodically
            self.cs += 1
            if self.cs >= 5:
                self.cs = 0
                utils.save_progress(self, title, content)

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

def _download_chapter_for_epub(self, title: str, chapter_id: str) -> epub.EpubHtml | None:
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
                f.write(f'{chapter_content.replace("\n", fg)}\n')
    return 's'

def _save_split_txt(self, name: str, content: dict) -> str:
    """Save each chapter to a separate TXT file"""
    output_dir = os.path.join(self.config.save_path, name)
    os.makedirs(output_dir, exist_ok=True)

    for title, chapter_content in content.items():
        chapter_path = os.path.join(
            output_dir,
            f'{utils.sanitize_filename(title)}.txt'
        )
        with open(chapter_path, 'w', encoding='UTF-8') as f:
            if self.config.kg == 0:
                f.write(f'{chapter_content}\n')
            else:
                f.write(
                    f'{chapter_content.replace("\n", self.config.kgf * self.config.kg)}\n'
                )
    return 's'

def html(self, novel_id: int) -> str:
    """Download novel in HTML format"""
    try:
        name, chapters, status = self._get_chapter_list(novel_id)
        if name == 'err':
            return 'err'

        safe_name = utils.sanitize_filename(name)
        html_dir = os.path.join(self.config.save_path, f"{safe_name}(html)")
        os.makedirs(html_dir, exist_ok=True)

        self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

        # Create index.html
        toc_content = format.html.index(name, chapters)
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

def latex(self, novel_id: int) -> str:
    """Download novel in LaTeX format"""
    try:
        name, chapters, status = self._get_chapter_list(novel_id)
        if name == 'err':
            return 'err'

        safe_name = utils.sanitize_filename(name)
        self.log_callback(f'\n开始下载《{name}》，状态：{status[0]}')

        # Create LaTeX document header
        latex_content = format.latex.header(name)

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
            latex_content += format.latex.chapter(title, content, self.config.kgf * self.config.kg)

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

def _download_chapter_for_html(self, title: str, chapter_id: str, output_dir: str, all_titles: list[str]) -> None:
    """Download and format chapter for HTML"""
    content = self._download_chapter(title, chapter_id, {})
    if not content:
        return

    current_index = all_titles.index(title)
    prev_link = f'<a href="{utils.sanitize_filename(all_titles[current_index-1])}.html">上一章</a>' if current_index > 0 else ''
    next_link = f'<a href="{utils.sanitize_filename(all_titles[current_index+1])}.html">下一章</a>' if current_index < len(all_titles)-1 else ''

    html_content = format.html.content(title, content, prev_link, next_link, self.config.kgf * self.config.kg)

    with open(os.path.join(output_dir, f"{utils.sanitize_filename(title)}.html"), "w", encoding='UTF-8') as f:
        f.write(html_content)

def _download_chapter_for_latex(self, title: str, chapter_id: str) -> str | None:
    """Download and format chapter for LaTeX"""
    content = self._download_chapter(title, chapter_id, {})
    if not content:
        return None
    return format.latex.chapter(title, content, self.config.kgf * self.config.kg)