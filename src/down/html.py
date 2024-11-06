import concurrent.futures, os
from tqdm import tqdm

from src import utils, format
from src.down import download



def html(self, novel_id: int) -> str:
    """Download novel in HTML format"""
    try:
        name, chapters, status = utils.get_chapter_list(self.headers, novel_id)
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
                        _download_chapter_for_html,
                        self,
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

def _download_chapter_for_html(self, title: str, chapter_id: str, output_dir: str, all_titles: list[str]) -> None:
    """Download and format chapter for HTML"""
    content = download.download_chapter(self, title, chapter_id, {})
    if not content:
        return

    current_index = all_titles.index(title)
    prev_link = f'<a href="{utils.sanitize_filename(all_titles[current_index-1])}.html">上一章</a>' if current_index > 0 else ''
    next_link = f'<a href="{utils.sanitize_filename(all_titles[current_index+1])}.html">下一章</a>' if current_index < len(all_titles)-1 else ''

    html_content = format.html.content(title, content, prev_link, next_link, self.config.kgf * self.config.kg)

    with open(os.path.join(output_dir, f"{utils.sanitize_filename(title)}.html"), "w", encoding='UTF-8') as f:
        f.write(html_content)