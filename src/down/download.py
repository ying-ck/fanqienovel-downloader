import time, json, os, random
import concurrent.futures
from tqdm import tqdm

from src.settings import SaveMode
from src import utils, cookie

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