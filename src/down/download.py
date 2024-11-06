import json
import time, random

import requests as req
from lxml import etree

from src import utils, cookie
from src.utils import decode_content
from src import settings

def chapter(self, title: str, chapter_id: str, existing_content: dict) -> str|None:
    """Download a single chapter with retries"""
    if title in existing_content:
        self.zj[title] = existing_content[title]  # Add this
        return existing_content[title]

    self.log_callback(f'下载章节: {title}')
    retries = 3
    last_error = None

    while retries > 0:
        try:
            content = chapter_content(self, chapter_id)
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
                utils.save_progress(title, content, self.zj, self.book_json_path)

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


def chapter_list(headers:dict, novel_id: int) -> tuple:
        """Get novel info and chapter list"""
        url = f'https://fanqienovel.com/page/{novel_id}'
        response = req.get(url, headers=headers)
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


def chapter_content(self, chapter_id: str, test_mode: bool = False) -> str:
    """Download content with fallback and better error handling"""
    headers = settings.headers.copy()
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
                return decode_content(content)
            except:
                # Try alternative decoding mode
                try:
                    return decode_content(content, mode=1)
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

                return decode_content(content)
            except:
                if attempt == 2:  # Last attempt
                    if test_mode:
                        return 'err'
                    raise Exception(f"Download failed after 3 attempts: {str(e)}")
                time.sleep(1)
