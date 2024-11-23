from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO, emit
from main import NovelDownloader, Config, SaveMode
import os
import threading
import queue
import zipfile
import io
import logging
from collections import deque
import time
import json
import sys
import re
from functools import wraps
import shutil
import concurrent.futures
from tqdm import tqdm
import traceback
from functools import lru_cache
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 首先创建配置实例
config = Config()

# 然后处理路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe运行
    BASE_DIR = sys._MEIPASS
    # 数据目录应该在exe所在目录
    DATA_ROOT = os.path.dirname(sys.executable)
    # 确保使用正确的路径分隔符
    DATA_ROOT = os.path.normpath(DATA_ROOT)
    
    # 修改下载器的保存路径
    config.save_path = os.path.join(DATA_ROOT, 'novel_downloads')
    config.bookstore_dir = os.path.join(DATA_ROOT, 'data', 'bookstore')
else:
    # 如果是源码运行
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_ROOT = BASE_DIR
    
    # 使用默认的保存路径
    config.save_path = os.path.join(DATA_ROOT, 'novel_downloads')
    config.bookstore_dir = os.path.join(DATA_ROOT, 'data', 'bookstore')

# 创建必要的目录
DATA_DIR = os.path.join(DATA_ROOT, 'data')
BOOKSTORE_DIR = os.path.join(DATA_DIR, 'bookstore')
DOWNLOADS_DIR = os.path.join(DATA_ROOT, 'novel_downloads')
CONFIG_FILE = os.path.join(DATA_DIR, 'web_config.json')

# 确保所有必要的目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BOOKSTORE_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# 打印路径信息以便调试
print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_ROOT: {DATA_ROOT}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"BOOKSTORE_DIR: {BOOKSTORE_DIR}")
print(f"DOWNLOADS_DIR: {DOWNLOADS_DIR}")

app = Flask(__name__,
            static_folder=os.path.join(BASE_DIR, 'static'),
            template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['SECRET_KEY'] = 'fanqie_novel_downloader'  # Add secret key
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins='*')

# Create downloads directory
downloads_dir = os.path.join(os.path.dirname(__file__), 'novel_downloads')
os.makedirs(downloads_dir, exist_ok=True)

# Create a global downloader instance with proper save path
config = Config()
config.save_path = DOWNLOADS_DIR  # 修改为 DOWNLOADS_DIR

# 修改下载器初始化部分
class NovelDownloaderWrapper(NovelDownloader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.book_json_path = None  # 添加这个属性
        self.zj = {}  # 确保这个属性被初始化
        self.cs = 0   # 确保这个属性被初始化
        self.tcs = 0  # 确保这个属性被初始化
        
    def download_novel(self, novel_id: int) -> str:
        try:
            name, chapters, status = self._get_chapter_list(novel_id)
            if name == 'err':
                return 'err'

            safe_name = _sanitize_filename(name)
            json_path = os.path.join(BOOKSTORE_DIR, f'{novel_id}_{safe_name}.json')
            txt_path = os.path.join(DOWNLOADS_DIR, f'{safe_name}.txt')
            
            logger.info(f"Will save JSON to: {json_path}")
            logger.info(f"Will save TXT to: {txt_path}")

            # 确保目录存在
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            os.makedirs(os.path.dirname(txt_path), exist_ok=True)

            # 下载章节内容
            chapter_list = sorted(chapters.items(), key=lambda x: int(re.search(r'\d+', x[0]).group() if re.search(r'\d+', x[0]) else '0'))
            total_chapters = len(chapter_list)
            completed_chapters = 0
            novel_content = {}

            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            self._download_chapter,
                            title,
                            chapter_id,
                            {}
                        ): (title, chapter_id, i) for i, (title, chapter_id) in enumerate(chapter_list)
                    }

                    results = [None] * total_chapters
                    for future in concurrent.futures.as_completed(future_to_chapter):
                        title, _, index = future_to_chapter[future]
                        try:
                            content = future.result()
                            if content:
                                results[index] = (title, content)
                                novel_content[title.strip()] = content
                        except Exception as e:
                            self.log_callback(f'下载章节失败 {title}: {str(e)}')

                        completed_chapters += 1
                        pbar.update(1)
                        self.progress_callback(
                            completed_chapters,
                            total_chapters,
                            '下载进度',
                            title
                        )

            # 在保存文件之前添加验证步骤
            logger.info("开始验证下载内容完整性")
            verified_content = verify_and_fix_chapters(
                novel_id, 
                name, 
                chapters, 
                novel_content,
                self
            )

            # 使用验证后的内容保存文件
            if config.save_mode == SaveMode.SINGLE_TXT:
                with open(txt_path, 'w', encoding='UTF-8') as f:
                    f.write(f"《{name}》\n\n")
                    # 按章节顺序写入
                    for title in chapters.keys():
                        content = verified_content.get(title)
                        if content:
                            f.write(f"\n{title}\n\n{content}\n")
                logger.info(f"Successfully saved TXT file to: {txt_path}")

            # 保存JSON文件
            try:
                novel_data = {
                    '_meta': {
                        'novel_id': novel_id,
                        'name': name,
                        'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'total_chapters': len(chapters),
                        'completed_chapters': len([c for c in verified_content.values() if c]),
                        'failed_chapters': verified_content.get('_failed_chapters', [])
                    },
                    'chapters': verified_content
                }
                
                with open(json_path, 'w', encoding='UTF-8') as f:
                    json.dump(novel_data, f, ensure_ascii=False, indent=4)
                logger.info(f"Successfully saved JSON file to: {json_path}")
                
                return 's'
            except Exception as e:
                logger.error(f"Failed to save JSON file: {str(e)}")
                return 'err'

        except Exception as e:
            self.log_callback(f'下载失败: {str(e)}')
            return 'err'

    def get_novel_content(self, novel_id: str) -> dict:
        """Get novel content from memory or file"""
        try:
            name, chapters, _ = self._get_chapter_list(novel_id)
            if name == 'err':
                return None
                
            safe_name = _sanitize_filename(name)
            json_path = os.path.join(BOOKSTORE_DIR, f'{novel_id}_{safe_name}.json')
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='UTF-8') as f:
                    data = json.load(f)
                    return data.get('chapters', {})  # 返回章节内容
            return None
        except Exception as e:
            logger.error(f"Error getting novel content: {str(e)}")
            return None

# 创建下载器实例
downloader = NovelDownloaderWrapper(
    config=config,
    progress_callback=lambda current, total, desc='', chapter='': socketio.emit('progress', {
        'current': current,
        'total': total,
        'percentage': round((current / total * 100) if total > 0 else 0, 2),
        'description': desc or '下载进度',
        'chapter': chapter,
        'text': f'已下载: {current}/{total} 章节 ({round((current / total * 100) if total > 0 else 0, 2)}%)'
    }),
    log_callback=lambda msg: socketio.emit('log', {'message': msg})
)

class DownloadQueue:
    def __init__(self):
        self.queue = deque()
        self.lock = threading.Lock()
        self.current_download = None
        self.downloading_ids = set()  # 添加一个集合来跟踪正在下载的ID
        self.completed_ids = set()    # 添加一个集合来跟踪已完成的下载
        
    def add(self, novel_id):
        with self.lock:
            # 检查是否已经下载成或正在下载
            if (novel_id not in self.queue and 
                novel_id not in self.downloading_ids and 
                novel_id not in self.completed_ids):
                self.queue.append(novel_id)
                logger.info(f"Added novel ID {novel_id} to download queue")
            else:
                logger.info(f"Novel ID {novel_id} is already in queue, downloading, or completed")
            
    def get_next(self):
        with self.lock:
            if self.queue:
                next_id = self.queue.popleft()
                self.downloading_ids.add(next_id)  # 添加到正在下载集合
                return next_id
            return None
            
    def finish_download(self, novel_id):
        with self.lock:
            if novel_id in self.downloading_ids:
                self.downloading_ids.remove(novel_id)
                self.completed_ids.add(novel_id)  # 添加到已完成集合
                logger.info(f"Finished downloading novel ID {novel_id}")
            
    def get_status(self):
        with self.lock:
            return {
                'queue_length': len(self.queue),
                'current_download': self.current_download,
                'queue_items': list(self.queue),
                'downloading': list(self.downloading_ids),
                'completed': list(self.completed_ids)
            }
    
    def clear_completed(self):
        """Clear completed downloads after some time"""
        with self.lock:
            self.completed_ids.clear()

# 创建全局下载队列实例
download_queue = DownloadQueue()

# 创建一个定时器来清理完成的下载记录
def clear_completed_downloads():
    while True:
        time.sleep(300)  # 每5分钟清理一次
        download_queue.clear_completed()

# 启动清理线程
threading.Thread(target=clear_completed_downloads, daemon=True).start()

def load_config():
    """Load saved configuration"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='UTF-8') as f:
                saved_config = json.load(f)
                
                # 更新配置
                config.kg = saved_config.get('kg', config.kg)
                config.kgf = saved_config.get('kgf', config.kgf)
                config.delay = saved_config.get('delay', config.delay)
                config.save_path = saved_config.get('save_path', DOWNLOADS_DIR)  # 使用默认的DOWNLOADS_DIR
                config.save_mode = SaveMode(saved_config.get('save_mode', config.save_mode.value))
                config.space_mode = saved_config.get('space_mode', config.space_mode)
                config.xc = saved_config.get('xc', config.xc)
                
                logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")

def save_config():
    """Save current configuration"""
    try:
        config_data = {
            'kg': config.kg,
            'kgf': config.kgf,
            'delay': config.delay,
            'save_path': config.save_path,
            'save_mode': config.save_mode.value,
            'space_mode': config.space_mode,
            'xc': config.xc
        }
        
        with open(CONFIG_FILE, 'w', encoding='UTF-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
            
        logger.info("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/novels')
def list_novels():
    """List downloaded novels with their status"""
    try:
        novels = []
        if os.path.exists(BOOKSTORE_DIR):
            for file in os.listdir(BOOKSTORE_DIR):
                if file.endswith('.json'):
                    try:
                        file_path = os.path.join(BOOKSTORE_DIR, file)
                        last_modified = os.path.getmtime(file_path)
                        last_modified_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified))
                        
                        # 从文件名中提取小说ID和名称
                        parts = file.split('_', 1)  # 分割一次，获取ID和名称
                        novel_id = parts[0]
                        novel_name = os.path.splitext(parts[1])[0] if len(parts) > 1 else os.path.splitext(file)[0]
                        
                        # 读取JSON文件获取章节数量
                        with open(file_path, 'r', encoding='UTF-8') as f:
                            data = json.load(f)
                            chapter_count = len(data.get('chapters', {}))
                            meta = data.get('_meta', {})
                            
                        novels.append({
                            'name': novel_name,
                            'status': f'已下载 {chapter_count} 章',
                            'last_updated': last_modified_str,
                            'novel_id': novel_id
                        })
                    except Exception as e:
                        logger.error(f"Error processing file {file}: {str(e)}")
                        continue
        
        return jsonify(novels)
    except Exception as e:
        logger.error(f"Error listing novels: {str(e)}")
        return jsonify([])

# 添加更好的错误处理装饰器
def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            logger.exception("Full traceback:")
            return jsonify({'error': str(e)}), 500
    return wrapper

def sort_chapters(chapters):
    """Sort chapters in correct order"""
    # 获取原始章节表
    name, original_chapters, _ = downloader._get_chapter_list(novel_id)
    if name == 'err':
        return chapters
        
    # 使用原始章节列表的顺序来排序
    sorted_chapters = {}
    for title in original_chapters.keys():
        if title in chapters:
            sorted_chapters[title] = chapters[title]
    
    # 添加可能存在的额外章节（不在原始列表中的）
    for title, content in chapters.items():
        if title not in sorted_chapters:
            sorted_chapters[title] = content
            
    return sorted_chapters

# 优化路由处理
@app.route('/api/download/<novel_id>')
@handle_errors
def download_novel(novel_id):
    """Download a novel by ID"""
    max_retries = 3  # 添加最大重试次数
    
    try:
        # 获取小说信息
        name, chapters, _ = downloader._get_chapter_list(novel_id)
        if name == 'err':
            return jsonify({'error': 'Novel not found'}), 404
            
        # 处理文件名，确保一致性
        safe_name = _sanitize_filename(name)
        json_path = os.path.join(BOOKSTORE_DIR, f'{novel_id}_{safe_name}.json')
        
        # 设置下载器的 book_json_path
        downloader.book_json_path = json_path  # 添加这一行
        
        # 根据保存模式设置不同的输出路径
        if config.save_mode == SaveMode.SINGLE_TXT:
            output_path = os.path.join(DOWNLOADS_DIR, f'{safe_name}.txt')
        elif config.save_mode == SaveMode.SPLIT_TXT:
            output_dir = os.path.join(DOWNLOADS_DIR, safe_name)
            os.makedirs(output_dir, exist_ok=True)
        elif config.save_mode == SaveMode.EPUB:
            output_path = os.path.join(DOWNLOADS_DIR, f'{safe_name}.epub')
        
        logger.info(f"Will save JSON to: {json_path}")
        if config.save_mode == SaveMode.EPUB:
            logger.info(f"Will save EPUB to: {output_path}")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        os.makedirs(DOWNLOADS_DIR, exist_ok=True)
        
        # 下载小说
        chapter_list = sorted(chapters.items(), key=lambda x: int(re.search(r'\d+', x[0]).group() if re.search(r'\d+', x[0]) else '0'))
        total_chapters = len(chapter_list)
        completed_chapters = 0
        novel_content = {}
        failed_chapters = []  # 记录下载失败的章节
        
        # 下载所有章节，失败的章节会重试
        retry_count = 0
        while True:
            with tqdm(total=total_chapters, desc='下载进度') as pbar:
                with concurrent.futures.ThreadPoolExecutor(max_workers=config.xc) as executor:
                    future_to_chapter = {
                        executor.submit(
                            downloader._download_chapter,
                            title,
                            chapter_id,
                            {}
                        ): (title, chapter_id, i) for i, (title, chapter_id) in enumerate(chapter_list)
                        if title not in novel_content  # 只下载未成功的章节
                    }

                    results = [None] * total_chapters
                    for future in concurrent.futures.as_completed(future_to_chapter):
                        title, chapter_id, index = future_to_chapter[future]
                        try:
                            content = future.result()
                            if content:
                                results[index] = (title, content)
                                novel_content[title.strip()] = content
                            else:
                                failed_chapters.append((title, chapter_id))
                        except Exception as e:
                            logger.error(f'下载章节失败 {title}: {str(e)}')
                            failed_chapters.append((title, chapter_id))

                        completed_chapters += 1
                        pbar.update(1)
                        socketio.emit('progress', {
                            'current': completed_chapters,
                            'total': total_chapters,
                            'percentage': round((completed_chapters / total_chapters * 100), 2),
                            'chapter': title
                        })

            # 如果没有失败的章节，退出循环
            if not failed_chapters:
                break
                
            # 检查重试次数
            retry_count += 1
            if retry_count >= max_retries:
                logger.warning(f"达到最大重试次数({max_retries})，仍有 {len(failed_chapters)} 个章节下载失败")
                break
                
            # 否则重试失败的章节
            logger.info(f"第 {retry_count} 次重试，重试 {len(failed_chapters)} 个失败的章节")
            chapter_list = failed_chapters
            failed_chapters = []
            total_chapters = len(chapter_list)
            completed_chapters = 0
            
            # 在重试前添加延迟
            time.sleep(2)

        # 根据保存模式保存文件
        if config.save_mode == SaveMode.SINGLE_TXT:
            with open(output_path, 'w', encoding='UTF-8') as f:
                f.write(f"《{name}》\n\n")
                for title, content in results:
                    if title and content:
                        f.write(f"\n{title}\n\n{content}\n")
            logger.info(f"Successfully saved TXT file to: {output_path}")
            
        elif config.save_mode == SaveMode.SPLIT_TXT:
            for title, content in results:
                if title and content:
                    chapter_file = os.path.join(output_dir, f'{title}.txt')
                    with open(chapter_file, 'w', encoding='UTF-8') as f:
                        f.write(f"{title}\n\n{content}")
            logger.info(f"Successfully saved split TXT files to: {output_dir}")
            
        elif config.save_mode == SaveMode.EPUB:
            # 创建EPUB文件
            from ebooklib import epub
            book = epub.EpubBook()
            book.set_title(name)
            book.set_language('zh')
            
            # 添加CSS样式
            style = '''
                @namespace epub "http://www.idpf.org/2007/ops";
                body {
                    font-family: "Microsoft YaHei", SimSun, serif;
                    line-height: 1.8;
                    margin: 2%;
                    padding: 0;
                }
                h1 {
                    text-align: center;
                    padding: 20px 0;
                    margin: 0;
                    font-weight: bold;
                }
                p {
                    text-indent: 2em;
                    margin: 0.8em 0;
                }
            '''
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            book.add_item(nav_css)
            
            chapters = []
            for i, (title, content) in enumerate(results):
                if title and content:
                    # 处理内容的换行和段落
                    paragraphs = content.split('\n')
                    formatted_content = '\n'.join([f'<p>{p}</p>' for p in paragraphs if p.strip()])
                    
                    chapter = epub.EpubHtml(title=title, file_name=f'chap_{i+1}.xhtml', lang='zh')
                    chapter.content = f'<h1>{title}</h1>\n{formatted_content}'
                    chapter.add_item(nav_css)
                    book.add_item(chapter)
                    chapters.append(chapter)

            # 添加目录
            book.toc = [(epub.Section(name), chapters)]
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            
            # 设置阅读顺序
            book.spine = ['nav'] + chapters
            
            # 保存EPUB文件
            epub.write_epub(output_path, book, {})
            logger.info(f"Successfully saved EPUB file to: {output_path}")

        # 保存JSON文件
        try:
            novel_data = {
                '_meta': {
                    'novel_id': novel_id,
                    'name': name,
                    'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_chapters': total_chapters,
                    'completed_chapters': len([r for r in results if r is not None])
                },
                'chapters': novel_content
            }
            
            with open(json_path, 'w', encoding='UTF-8') as f:
                json.dump(novel_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Successfully saved JSON file to: {json_path}")
            
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Failed to save JSON file: {str(e)}")
            return jsonify({'error': 'Failed to save novel file'}), 500

    except Exception as e:
        logger.error(f"Error downloading novel: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

# 添加基本的安全检查
def sanitize_input(text):
    return re.sub(r'[<>:"/\\|?*]', '', text)

@app.route('/api/search')
def search_novels():
    keyword = request.args.get('keyword', '')
    results = downloader.search_novel(keyword)
    return jsonify(results)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        try:
            data = request.json
            config.kg = data.get('kg', config.kg)
            config.kgf = data.get('kgf', config.kgf)
            config.delay = data.get('delay', config.delay)
            config.save_mode = SaveMode(data.get('save_mode', config.save_mode.value))
            config.xc = data.get('xc', config.xc)
            
            # 保存设置到文件
            save_config()
            
            return jsonify({'status': 'success'})
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    return jsonify({
        'kg': config.kg,
        'kgf': config.kgf,
        'delay': config.delay,
        'save_mode': config.save_mode.value,
        'xc': config.xc
    })

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a novel file"""
    if filename.endswith('(html).zip'):
        # Create ZIP file for HTML format
        novel_name = filename[:-9]  # Remove (html).zip
        html_dir = os.path.join(downloads_dir, f"{novel_name}(html)")
        if os.path.exists(html_dir):
            memory_file = io.BytesIO()
            with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(html_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, html_dir)
                        zf.write(file_path, arcname)
            memory_file.seek(0)
            return send_file(
                memory_file,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )
    else:
        filepath = os.path.join(downloads_dir, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/components/<template>')
def get_component(template):
    """Serve component templates"""
    try:
        # 确保template参数包含.html扩展名
        if not template.endswith('.html'):
            template += '.html'
        app.logger.info(f"Loading template: components/{template}")
        
        # 如果是阅读器页面，返回完整的HTML
        if template == 'reader.html':
            return render_template(f'components/{template}')
        
        # 对于其他组件，返回片段
        return render_template(f'components/{template}', layout=False)
        
    except Exception as e:
        app.logger.error(f"Error loading template {template}: {str(e)}")
        return f"Error loading template: {str(e)}", 404

@app.route('/api/update-all', methods=['POST'])
def update_all():
    """Update all novels in the library"""
    try:
        # Add to download queue
        novels = downloader.get_downloaded_novels()
        update_count = 0
        for novel in novels:
            if novel.get('novel_id'):
                download_queue.add(novel['novel_id'])
                update_count += 1
        
        if update_count > 0:
            socketio.emit('log', {'message': f'已添加 {update_count} 小说到更新队列'})
            return jsonify({'status': 'queued', 'count': update_count})
        else:
            socketio.emit('log', {'message': '没有找到可以更新的小说'})
            return jsonify({'status': 'no_novels'})
            
    except Exception as e:
        error_msg = f'更新失败: {str(e)}'
        socketio.emit('log', {'message': error_msg})
        return jsonify({'error': error_msg}), 500

@app.route('/api/queue/status')
def get_queue_status():
    return jsonify(download_queue.get_status())

@app.route('/api/queue/add/<novel_id>', methods=['POST'])
def add_to_queue(novel_id):
    download_queue.add(novel_id)
    # 广播队列更新给所有客户端
    socketio.emit('queue_update', download_queue.get_status())
    return jsonify({'status': 'success'})

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    # Windows不允许的字符: \ / : * ? " < > |
    # 只替换这些Windows不支持的字符，保留中文标点
    filename = filename.strip()
    
    # 只替换Windows不允许的字符和一些特殊字符
    replacements = {
        '/': '／',  # 使用全角斜杠
        '\\': '＼', # 使用全角反斜杠
        ':': '：',  # 使用中文冒号
        '*': '＊',  # 使用全角星号
        '?': '？',  # 使用中文问号
        '"': '"',   # 使用中文引号
        '<': '＜',  # 使用全角小于号
        '>': '＞',  # 使用全角大于号
        '|': '｜',  # 使用全角竖线
        '\n': '',   # 移除换行符
        '\r': '',   # 移除回车符
        '\t': ' ',  # 制表符替换为空格
    }
    
    for old, new in replacements.items():
        filename = filename.replace(old, new)
    
    # 移除开头和结尾的空格
    filename = filename.strip()
    
    # 确保文件名不为空
    if not filename:
        filename = 'untitled'
        
    # 限制文件名长度
    if len(filename) > 100:
        filename = filename[:100]
        
    return filename

@app.route('/api/read/<novel_id>/<chapter_title>')
def read_chapter(novel_id, chapter_title):
    """API endpoint to read a specific chapter of a novel"""
    try:
        logger.info(f"Attempting to read chapter: {chapter_title} from novel: {novel_id}")
        
        # 首先确保小说已下载
        if not os.path.exists(BOOKSTORE_DIR):
            logger.error(f"Bookstore directory not found: {BOOKSTORE_DIR}")
            os.makedirs(BOOKSTORE_DIR, exist_ok=True)
            
        # 获取小说信息
        name, chapters, _ = downloader._get_chapter_list(novel_id)
        if name == 'err':
            return jsonify({'error': 'Novel not found'}), 404
            
        # 处理文件名，确保一致性
        safe_name = _sanitize_filename(name)
        json_path = os.path.join(BOOKSTORE_DIR, f'{novel_id}_{safe_name}.json')  # 使用带ID的文件名
        logger.info(f"Looking for JSON file at: {json_path}")
        
        # 如果文件不存在，等待下载完成
        if not os.path.exists(json_path):
            # 检查是否已经在下载
            if novel_id not in download_queue.downloading_ids and novel_id not in download_queue.queue:
                logger.info(f"Novel file not found, adding to download queue: {novel_id}")
                download_queue.add(novel_id)
                socketio.emit('queue_update', download_queue.get_status())
            
            # 等待下载完成
            while novel_id in download_queue.downloading_ids or novel_id in download_queue.queue:
                time.sleep(0.5)
            
            # 再次检查文件是否存在
            if not os.path.exists(json_path):
                logger.error(f"JSON file still not found after download: {json_path}")
                return jsonify({'error': 'Failed to create novel file'}), 500
        
        # 读取JSON文件
        try:
            with open(json_path, 'r', encoding='UTF-8') as f:
                novel_data = json.load(f)
                # 从 novel_data 中获取章节内容
                chapters_data = novel_data.get('chapters', {})
                chapter_content = chapters_data.get(chapter_title)
                
                if chapter_content is None:
                    logger.error(f"Chapter not found: {chapter_title}")
                    return jsonify({'error': 'Chapter not found'}), 404
                    
                return jsonify({
                    'title': chapter_title,
                    'content': chapter_content
                })
                
        except Exception as e:
            logger.error(f"Error reading JSON file: {str(e)}")
            return jsonify({'error': 'Failed to read novel data'}), 500

    except Exception as e:
        logger.error(f"Error reading chapter: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

def process_download_queue():
    while True:
        novel_id = download_queue.get_next()
        if novel_id:
            download_queue.current_download = novel_id
            socketio.emit('queue_update', download_queue.get_status())
            try:
                with app.app_context():
                    try:
                        downloader.download_novel(novel_id)
                        socketio.emit('log', {'message': f'小说 {novel_id} 下载完成'})
                    except Exception as e:
                        socketio.emit('log', {'message': f'下载失败: {str(e)}'})
            finally:
                download_queue.current_download = None
                download_queue.finish_download(novel_id)  # 标记下载完成
                socketio.emit('queue_update', download_queue.get_status())
        time.sleep(1)

# 启动队列处理线程
threading.Thread(target=process_download_queue, daemon=True).start()

def print_server_info():
    """Print server access information"""
    logger.info("""
────────────────────────────────────────────────
│                                                  │
│   番茄小说下载器 Web 服务已启动                      │
│                                                  │
│   请在浏览器中访问:                                 │
│   http://localhost:12930                         │
│                                                  │
│   如果需要从其他设备访问，请使用:                     │
│   http://<本机IP>:12930                           │
│                                                  │
╰──────────────────────────────────────────────────╯
    """)

@app.route('/api/chapters/<novel_id>')
@handle_errors
def get_chapters(novel_id):
    """Get chapter list for a novel"""
    try:
        name, chapters, status = downloader._get_chapter_list(novel_id)
        if name == 'err':
            raise Exception('Novel not found')
            
        # 将章节信息转换为列表格式并排序
        chapter_list = []
        for title, chapter_id in chapters.items():
            try:
                # 提取章节号，支持多种格式
                match = re.search(r'(?:第|^)(\d+)(?:章|节|集|卷|部|篇|回|话)', title)
                if match:
                    chapter_num = int(match.group(1))
                else:
                    # 尝试直接提取数字
                    numbers = re.findall(r'\d+', title)
                    chapter_num = int(numbers[0]) if numbers else float('inf')
            except:
                chapter_num = float('inf')
                
            chapter_list.append({
                'title': title,
                'id': chapter_id,
                'chapter_num': chapter_num,
                'original_index': len(chapter_list)
            })
        
        # 首先按章节号排序
        chapter_list.sort(key=lambda x: x['chapter_num'])
        
        # 对于章节号相同的情况，按原始顺序排序
        chapter_list.sort(key=lambda x: (x['chapter_num'], x['original_index']))
        
        # 移除辅助字段
        for chapter in chapter_list:
            del chapter['original_index']
            del chapter['chapter_num']
        
        return jsonify({
            'name': name,
            'chapters': chapter_list,
            'status': status[0] if status else None
        })
    except Exception as e:
        logger.error(f"Error getting chapters: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

# 添加更详细的错误日志
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {str(error)}")
    logger.exception("Full traceback:")
    return jsonify({
        'error': str(error),
        'details': traceback.format_exc()
    }), 500

@lru_cache(maxsize=100)
def get_chapter_content(novel_id, chapter_title):
    try:
        name, chapters, _ = downloader._get_chapter_list(novel_id)
        if name == 'err':
            return None
            
        safe_name = _sanitize_filename(name)
        json_path = os.path.join(BOOKSTORE_DIR, f'{safe_name}.json')
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='UTF-8') as f:
                novel_data = json.load(f)
                return novel_data.get(chapter_title)
        return None
    except Exception as e:
        logger.error(f"Error getting chapter content: {str(e)}")
        return None

def save_progress(novel_id, name, novel_content):
    """保存下载进度到JSON文件"""
    try:
        safe_name = _sanitize_filename(name)
        json_path = os.path.join(BOOKSTORE_DIR, f'{novel_id}_{safe_name}.json')
        
        novel_data = {
            '_meta': {
                'novel_id': novel_id,
                'name': name,
                'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_chapters': len(novel_content)
            },
            'chapters': novel_content
        }
        
        with open(json_path, 'w', encoding='UTF-8') as f:
            json.dump(novel_data, f, ensure_ascii=False, indent=4)
            
        logger.info(f"Progress saved to: {json_path}")
    except Exception as e:
        logger.error(f"Error saving progress: {str(e)}")

def sort_chapter_list(chapter_list):
    """改进的章节排序逻辑"""
    def extract_chapter_number(title):
        # 尝试多种匹配模式
        patterns = [
            r'第(\d+)章',
            r'第(\d+)节',
            r'(\d+)',
            r'第([一二三四五六七八九十百千万]+)章'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                num = match.group(1)
                if num.isdigit():
                    return int(num)
                # 处理中文数字
                return cn2num(num) if any(c in num for c in '一二三四五六七八九十百千万') else float('inf')
        return float('inf')
    
    def cn2num(cn):
        """将中文数字转换为阿拉伯数字"""
        cn_num = {'一':1, '二':2, '三':3, '四':4, '五':5, 
                 '六':6, '七':7, '八':8, '九':9, '十':10,
                 '百':100, '千':1000, '万':10000}
        # 简单转换逻辑，可以根据需要扩展
        if len(cn) == 1:
            return cn_num.get(cn, float('inf'))
        return float('inf')
    
    # 排序
    return sorted(chapter_list, key=lambda x: (extract_chapter_number(x[0]), chapter_list.index(x)))

def check_chapter_content(content: str) -> bool:
    """检查章节内容是否完整有效"""
    if not content:
        return False
    # 检查内容是否太短（可能是下载失败）
    if len(content) < 100:  # 假设正常章节至少有100个字符
        return False
    # 检查是否包含常见的错误标记
    error_markers = ['下载失败', '获取失败', '请求失败', '访问太频繁']
    return not any(marker in content for marker in error_markers)

def verify_and_fix_chapters(novel_id: str, name: str, chapters: dict, novel_content: dict, downloader) -> dict:
    """验证章节完整性并修复缺失或损坏的章节"""
    logger.info(f"开始验证章节完整性: {name}")
    fixed_content = novel_content.copy()
    failed_chapters = []
    
    # 检查每个章节
    for title, chapter_id in chapters.items():
        content = novel_content.get(title)
        if not content or not check_chapter_content(content):
            logger.warning(f"发现问题章节: {title}")
            failed_chapters.append((title, chapter_id))
            
    # 如果有问题章节，尝试重新下载
    if failed_chapters:
        logger.info(f"发现 {len(failed_chapters)} 个问题章节，开始修复")
        max_retries = 3
        retry_count = 0
        
        while failed_chapters and retry_count < max_retries:
            retry_count += 1
            logger.info(f"第 {retry_count} 次尝试修复")
            
            still_failed = []
            for title, chapter_id in failed_chapters:
                try:
                    logger.info(f"重新下载章节: {title}")
                    content = downloader._download_chapter(title, chapter_id, {})
                    if content and check_chapter_content(content):
                        fixed_content[title] = content
                        logger.info(f"成功修复章节: {title}")
                    else:
                        still_failed.append((title, chapter_id))
                except Exception as e:
                    logger.error(f"修复章节失败 {title}: {str(e)}")
                    still_failed.append((title, chapter_id))
                
                # 添加延迟避免请求过快
                time.sleep(random.randint(1, 3))
            
            failed_chapters = still_failed
            
            if failed_chapters:
                logger.warning(f"仍有 {len(failed_chapters)} 个章节修复失败，等待后重试")
                time.sleep(5)  # 较长的等待时间
    
    # 保存修复后的内容
    if failed_chapters:
        logger.warning(f"最终仍有 {len(failed_chapters)} 个章节未能修复")
        # 记录未修复的章节信息
        fixed_content['_failed_chapters'] = [title for title, _ in failed_chapters]
    else:
        logger.info("所有章节验证完成，内容完整")
        
    return fixed_content

if __name__ == '__main__':
    # 加载保存的配置
    load_config()
    
    # Disable Flask's debug mode but keep SocketIO's debug mode
    app.debug = False
    
    # Print server info
    print_server_info()
    
    # Run the server
    socketio.run(
        app,
        host='0.0.0.0',
        port=12930,
        debug=False,
        use_reloader=False
    )
