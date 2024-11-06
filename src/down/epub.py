from ebooklib import epub
import concurrent.futures, os
from tqdm import tqdm
from src import utils, format
from src.down import download

def depub(self, novel_id: int) -> str:
    """Download novel in EPUB format"""
    try:
        name, chapters, status = download.get_chapter_list(self.headers, novel_id)
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
                        _download_chapter_for_epub,
                        self,
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

def _download_chapter_for_epub(self, title: str, chapter_id: str) -> epub.EpubHtml | None:
    """Download and format chapter for EPUB"""
    content = download._download_chapter(self, title, chapter_id, {})
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