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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fanqie_novel_downloader'  # Add secret key
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins='*')

# Create a global downloader instance
config = Config()
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

# Queue for download tasks
download_queue = queue.Queue()

def download_worker():
    while True:
        task = download_queue.get()
        if task is None:
            break
        novel_id = task
        try:
            downloader.download_novel(novel_id)
        except Exception as e:
            socketio.emit('log', {'message': f'下载失败: {str(e)}'})
        download_queue.task_done()

# Start worker thread
worker_thread = threading.Thread(target=download_worker, daemon=True)
worker_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/novels')
def list_novels():
    novels = downloader.get_downloaded_novels()
    return jsonify(novels)

@app.route('/api/download/<novel_id>')
def download_novel(novel_id):
    download_queue.put(novel_id)
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
        html_dir = os.path.join(downloader.config.save_path, f"{novel_name}(html)")
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
        filepath = os.path.join(downloader.config.save_path, filename)
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

def print_server_info():
    """Print server access information"""
    logger.info("""
╭──────────────────────────────────────────────────╮
│                                                  │
│   番茄小说下载器 Web 服务已启动                 │
│                                                  │
│   请在浏览器中访问:                             │
│   http://localhost:12930                         │
│                                                  │
│   如果需要从其他设备访问，请使用:               │
│   http://<本机IP>:12930                         │
│                                                  │
╰───────────────────────────────────────��─────────╯
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
