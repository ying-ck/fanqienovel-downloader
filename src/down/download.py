import time, random
from src import utils, cookie


def download_chapter(self, title: str, chapter_id: str, existing_content: dict) -> str|None:
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
