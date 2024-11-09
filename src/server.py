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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__,
            static_folder=os.path.join(os.path.dirname(__file__), 'static'),
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.config['SECRET_KEY'] = 'fanqie_novel_downloader'  # Add secret key
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins='*')

# Create downloads directory
downloads_dir = os.path.join(os.path.dirname(__file__), 'novel_downloads')
os.makedirs(downloads_dir, exist_ok=True)

# Create a global downloader instance with proper save path
config = Config()
config.save_path = downloads_dir  # Set save path to downloads directory

downloader = NovelDownloader(
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
        
    def add(self, novel_id):
        with self.lock:
            self.queue.append(novel_id)
            
    def get_next(self):
        with self.lock:
            return self.queue.popleft() if self.queue else None
            
    def get_status(self):
        with self.lock:
            return {
                'queue_length': len(self.queue),
                'current_download': self.current_download,
                'queue_items': list(self.queue)
            }

# 创建全局下载队列实例
download_queue = DownloadQueue()

# 添加配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'data', 'web_config.json')

# 确保配置目录存在
os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

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
                config.save_path = saved_config.get('save_path', config.save_path)
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
    novels = downloader.get_downloaded_novels()
    return jsonify(novels)

@app.route('/api/download/<novel_id>')
def download_novel(novel_id):
    download_queue.add(novel_id)
    socketio.emit('queue_update', download_queue.get_status())
    return jsonify({'status': 'queued'})

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
            socketio.emit('log', {'message': f'已添加 {update_count} 本小说到更新队列'})
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

@app.route('/api/read/<novel_id>/<chapter_title>')
def read_chapter(novel_id, chapter_title):
    """API endpoint to read a specific chapter of a novel"""
    try:
        logger.info(f"Attempting to read chapter: {chapter_title} from novel: {novel_id}")
        
        # 首先确保小说已下载
        if not os.path.exists(downloader.bookstore_dir):
            logger.error("Bookstore directory does not exist")
            return jsonify({'error': 'Bookstore directory not found'}), 404
            
        # 查找小说文件
        novel_files = [f for f in os.listdir(downloader.bookstore_dir) 
                      if f.endswith('.json')]
        logger.info(f"Found novel files: {novel_files}")
        
        novel_file = None
        for file in novel_files:
            with open(os.path.join(downloader.bookstore_dir, file), 'r', encoding='UTF-8') as f:
                data = json.load(f)
                if '_metadata' in data and data['_metadata'].get('novel_id') == str(novel_id):
                    novel_file = file
                    break
        
        if not novel_file:
            logger.error(f"Novel file not found for ID: {novel_id}")
            return jsonify({'error': 'Novel not found'}), 404

        # 读取小说内容
        novel_path = os.path.join(downloader.bookstore_dir, novel_file)
        logger.info(f"Reading novel file: {novel_path}")
        
        with open(novel_path, 'r', encoding='UTF-8') as f:
            novel_data = json.load(f)

        # 获取章节内容
        chapter_content = novel_data.get(chapter_title)
        if not chapter_content:
            logger.error(f"Chapter not found: {chapter_title}")
            return jsonify({'error': 'Chapter not found'}), 404

        logger.info(f"Successfully retrieved chapter content for: {chapter_title}")
        return jsonify({
            'title': chapter_title,
            'content': chapter_content
        })

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
                # 在应用上下文中执行下载逻辑
                with app.app_context():
                    # 直接调用下载器而不是函数
                    try:
                        downloader.download_novel(novel_id)
                        socketio.emit('log', {'message': f'小说 {novel_id} 下载完成'})
                    except Exception as e:
                        socketio.emit('log', {'message': f'下载失败: {str(e)}'})
            finally:
                download_queue.current_download = None
                socketio.emit('queue_update', download_queue.get_status())
        time.sleep(1)

# 启动队列处理线程
threading.Thread(target=process_download_queue, daemon=True).start()

def print_server_info():
    """Print server access information"""
    logger.info("""
╭──────────────────────────────────────────────────
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
def get_chapters(novel_id):
    """Get chapter list for a novel"""
    try:
        logger.info(f"Attempting to download novel with ID: {novel_id}")
        download_status = downloader.download_novel(novel_id)
        logger.info(f"Download status: {download_status}")
        
        if not download_status:
            logger.error(f"Failed to download novel with ID: {novel_id}")
            return jsonify({'error': 'Failed to download novel'}), 404

        name, chapters, status = downloader._get_chapter_list(novel_id)
        logger.info(f"Got chapter list: {len(chapters)} chapters")
        
        if name == 'err':
            logger.error(f"Novel not found with ID: {novel_id}")
            return jsonify({'error': 'Novel not found'}), 404

        chapter_list = [{'title': title, 'id': chapter_id} for title, chapter_id in chapters.items()]
        
        json_path = os.path.join(downloader.bookstore_dir, f'{novel_id}.json')
        logger.info(f"Checking JSON file: {json_path}")
        
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='UTF-8') as f:
                novel_data = json.load(f)
                if '_metadata' in novel_data:
                    del novel_data['_metadata']
                for chapter in chapter_list:
                    chapter['content'] = novel_data.get(chapter['title'], '')

        logger.info(f"Successfully retrieved chapters for novel ID: {novel_id}")
        return jsonify({
            'name': name,
            'chapters': chapter_list,
            'status': status[0] if status else None
        })

    except Exception as e:
        logger.error(f"Error getting chapters for novel ID {novel_id}: {str(e)}")
        logger.exception("Full traceback:")
        return jsonify({'error': str(e)}), 500

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
