from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, send_file, request
from flask_socketio import SocketIO
from tmp import NovelDownloader
from src.settings import Config, SaveMode
import os, threading, zipfile, io, logging, time
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
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
        data = request.json
        config.kg = data.get('kg', config.kg)
        config.kgf = data.get('kgf', config.kgf)
        config.delay = data.get('delay', config.delay)
        config.save_mode = SaveMode(data.get('save_mode', config.save_mode.value))
        config.xc = data.get('xc', config.xc)
        return jsonify({'status': 'success'})
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

@app.route('/templates/components/<template>')
def get_component(template):
    """Serve component templates"""
    try:
        return render_template(f'components/{template}')
    except Exception as e:
        return str(e), 404

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

def process_download_queue():
    while True:
        novel_id = download_queue.get_next()
        if novel_id:
            download_queue.current_download = novel_id
            socketio.emit('queue_update', download_queue.get_status())
            try:
                # 在应用上下文中执行下载逻辑
                with app.app_context():
                    # 直接调用下载器而不是调用路由函数
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
╭──────────────────────────────────────────────────╮
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

if __name__ == '__main__':
    # Disable Flask's debug mode but keep SocketIO's debug mode
    app.debug = False
    
    # Print server info
    print_server_info()
    
    # Run the server
    socketio.run(
        app,
        host='0.0.0.0',
        port=12930,
        debug=False,  # Disable debug mode
        use_reloader=False  # Disable reloader
    )
