import concurrent.futures, os
from tqdm import tqdm

from src import utils, format, settings
from src.down import download

def latex(self, novel_id: int) -> str:
    """Download novel in LaTeX format"""
    try:
        name, chapters, status = download.chapter_list(settings.headers, novel_id)
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
                        _download_chapter_for_latex,
                        self,
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

def _download_chapter_for_latex(self, title: str, chapter_id: str) -> str | None:
    """Download and format chapter for LaTeX"""
    content = download.chapter(self, title, chapter_id, {})
    if not content:
        return None
    return format.latex.chapter(title, content, self.config.kgf * self.config.kg)