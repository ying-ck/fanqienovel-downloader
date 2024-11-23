function loadPage(url) {
    if (url.includes('reader.html')) {
        // 对于阅读器页面，直接替换整个内容
        window.location.href = url;
    } else {
        // 对于其他页面，使用 AJAX 加载
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                document.getElementById('content').innerHTML = html;
                initializePage();
            })
            .catch(error => {
                console.error('Error loading page:', error);
                document.getElementById('content').innerHTML = `
                    <div class="alert alert-danger">
                        加载页面失败: ${error.message}
                    </div>`;
            });
    }
}

function initializePage() {
    // 根据当前加载的页面执行特定的初始化代码
    const content = document.getElementById('content');
    
    // 搜索页面初始化
    if (content.querySelector('.search-container')) {
        initializeSearch();
    }
    // 书库页面初始化
    else if (content.querySelector('.library-container')) {
        initializeLibrary();
    }
    // 设置页面初始化
    else if (content.querySelector('.settings-container')) {
        initializeSettings();
    }
    // 阅读页面初始化
    else if (content.querySelector('.reader-container')) {
        initializeReader();
    }
}

// 页面加载完成后初始化导航事件监听
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载非关键资源
    setTimeout(() => {
        // 加载 Socket.IO
        const script = document.createElement('script');
        script.src = 'https://cdn.socket.io/4.0.1/socket.io.min.js';
        document.body.appendChild(script);
        
        script.onload = () => {
            initializeSocketIO();
        };
    }, 100);

    // 默认加载搜索页面
    loadPage('components/search.html');

    // 设置导航链接点击事件
    document.querySelectorAll('[data-page]').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            
            // 如果是阅读页面，先提示输入小说ID
            if (page === 'reader') {
                const novelId = prompt('请输入小说ID:');
                if (novelId && novelId.trim()) {  // 检查ID是否有效
                    // 使用 loadPage 而不是直接改变 location
                    loadPage(`components/reader.html?novel_id=${novelId}`);
                    
                    // 更新 URL，但不刷新页面
                    window.history.pushState(
                        { novelId: novelId }, 
                        '', 
                        `/components/reader.html?novel_id=${novelId}`
                    );
                } else {
                    // 如果用户取消或输入无效ID，返回到之前的页面
                    return;
                }
            } else {
                loadPage(`components/${page}.html`);
            }
            
            // 更新活动导航项
            document.querySelectorAll('.nav-link').forEach(navLink => {
                navLink.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
    
    // 处理浏览器的后退/前进按钮
    window.addEventListener('popstate', function(event) {
        if (event.state && event.state.novelId) {
            loadPage(`components/reader.html?novel_id=${event.state.novelId}`);
        }
    });
});

// 将下载相关函数移到全局作用域
function downloadNovel(novelId) {
    // 先显示进度模态框
    showProgressModal();
    
    fetch(`/api/download/${novelId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('下载失败: ' + data.error);
                // 如果下载失败，关闭进度模态框
                const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
                if (progressModal) {
                    progressModal.hide();
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('下载失败，请检查控制台获取详细信息');
            // 如果发生错误，关闭进度模态框
            const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
            if (progressModal) {
                progressModal.hide();
            }
        });
}

// 直接下载功能
function downloadDirect() {
    const input = document.getElementById('directInput').value.trim();
    if (!input) {
        alert('请输入小说ID或链接');
        return;
    }
    
    // 提取ID（如果是链接的话）
    const id = input.includes('/') ? input.split('/').pop() : input;
    
    // 调用下载函数
    downloadNovel(id);
}

// 显示进度模态框函数
function showProgressModal() {
    const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
    if (progressModal) {
        // 重置进度条和日志
        document.querySelector('.progress-bar').style.width = '0%';
        document.querySelector('.progress-bar').textContent = '0%';
        document.getElementById('currentChapter').textContent = '';
        document.getElementById('logOutput').textContent = '';
        progressModal.show();
    } else {
        // 如果实例不存在，创建新的实例
        const newModal = new bootstrap.Modal(document.getElementById('progressModal'), {
            backdrop: true,  // 允许点击背景关闭
            keyboard: true   // 允许按 ESC 键关闭
        });
        newModal.show();
    }
    document.getElementById('showProgress').classList.add('d-none');
}

// 监听 Socket.IO 事件
function initializeSocketIO() {
    const socket = io();
    
    socket.on('progress', function(data) {
        const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (!progressModal) {
            showProgressModal();
        }
        
        const progressBar = document.querySelector('.progress-bar');
        const currentChapter = document.getElementById('currentChapter');
        
        progressBar.style.width = data.percentage + '%';
        progressBar.textContent = data.percentage.toFixed(1) + '%';
        
        if (data.chapter) {
            currentChapter.textContent = `当前章节: ${data.chapter}`;
        }
        
        // 如果下载完成，允许关闭模态框
        if (data.percentage >= 100) {
            const modalElement = document.getElementById('progressModal');
            modalElement.setAttribute('data-bs-backdrop', 'true');
            modalElement.setAttribute('data-bs-keyboard', 'true');
        }
    });

    // 监听日志消息
    socket.on('log', function(data) {
        const logOutput = document.getElementById('logOutput');
        logOutput.textContent += data.message + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;
    });

    // 监听队列更新
    socket.on('queue_update', function(data) {
        const currentChapter = document.getElementById('currentChapter');
        const queueStatus = document.createElement('div');
        queueStatus.className = 'queue-status';
        queueStatus.textContent = `队列中: ${data.queue_length} 本小说`;
        
        // 清除旧的队列状���
        const oldStatus = currentChapter.querySelector('.queue-status');
        if (oldStatus) {
            oldStatus.remove();
        }
        
        currentChapter.appendChild(queueStatus);
    });

    // 监听显示进度模态框的事件
    socket.on('show_progress', function() {
        showProgressModal();
    });
}

// 初始化搜索页面
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const keyword = searchInput.value.trim();
            if (keyword) {
                fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`)
                    .then(response => response.json())
                    .then(data => {
                        displaySearchResults(data);
                    })
                    .catch(error => console.error('Error:', error));
            }
        });
    }

    // 添加回车键搜索支持
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }
}

function initializeLibrary() {
    const updateAllBtn = document.getElementById('updateAllBtn');
    if (updateAllBtn) {
        updateAllBtn.addEventListener('click', () => {
            fetch('/api/update-all', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'queued') {
                        alert(`已添加 ${data.count} 本小说到更新队列`);
                    }
                })
                .catch(error => console.error('Error:', error));
        });
    }
    
    // 加载已下载的小说列表
    loadDownloadedNovels();
}

function initializeSettings() {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        // 加载当前设置
        fetch('/api/settings')
            .then(response => response.json())
            .then(data => {
                document.getElementById('kgf').value = data.kgf;
                document.getElementById('kg').value = data.kg;
                document.getElementById('delayMin').value = data.delay[0];
                document.getElementById('delayMax').value = data.delay[1];
                document.getElementById('saveMode').value = data.save_mode;
                document.getElementById('xc').value = data.xc;
            });

        settingsForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = {
                kgf: document.getElementById('kgf').value,
                kg: parseInt(document.getElementById('kg').value),
                delay: [
                    parseInt(document.getElementById('delayMin').value),
                    parseInt(document.getElementById('delayMax').value)
                ],
                save_mode: parseInt(document.getElementById('saveMode').value),
                xc: parseInt(document.getElementById('xc').value)
            };

            fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('设置已保存');
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
}

function initializeReader() {
    // 阅读器功能已在 reader.html 中实现
}

// 辅助函数
function loadDownloadedNovels() {
    fetch('/api/novels')
        .then(response => response.json())
        .then(novels => {
            const novelList = document.getElementById('novelList');
            if (novelList) {
                novelList.innerHTML = novels.map(novel => `
                    <div class="col-md-4 mb-3">
                        <div class="card shadow-sm h-100">
                            <div class="card-body">
                                <h5 class="card-title text-primary">
                                    <i class="bi bi-book"></i> ${novel.name}
                                </h5>
                                <div class="card-text">
                                    <p class="mb-2">
                                        <i class="bi bi-info-circle"></i> 状态: ${novel.status || '未知'}
                                    </p>
                                    <p class="mb-2">
                                        <i class="bi bi-clock"></i> 最后更新: ${novel.last_updated || '未知'}
                                    </p>
                                </div>
                                <div class="btn-group">
                                    <button class="btn btn-dark btn-sm" 
                                            onclick="window.location.href='components/reader.html?novel_id=${novel.novel_id}'">
                                        <i class="bi bi-book-half"></i> 阅读
                                    </button>
                                    <button class="btn btn-outline-dark btn-sm" 
                                            onclick="downloadNovel('${novel.novel_id}')">
                                        <i class="bi bi-arrow-clockwise"></i> 更新
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        })
        .catch(error => console.error('Error:', error));
}

// 修改搜索结果显示函数
function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        if (!results || results.length === 0) {
            searchResults.innerHTML = `
                <div class="col">
                    <div class="alert alert-info">
                        <i class="bi bi-info-circle"></i> 没有找到相关小说
                    </div>
                </div>`;
            return;
        }

        searchResults.innerHTML = results.map(result => `
            <div class="col-md-6 mb-3">
                <div class="card shadow-sm">
                    <div class="card-body">
                        <h5 class="card-title text-primary">
                            <i class="bi bi-book"></i> ${result.book_data[0].book_name}
                        </h5>
                        <p class="card-text">
                            <i class="bi bi-person"></i> 作者: ${result.book_data[0].author}<br>
                            <i class="bi bi-file-text"></i> 字数: ${result.book_data[0].word_number}
                        </p>
                        <button class="btn btn-dark btn-sm" 
                                onclick="downloadNovel('${result.book_data[0].book_id}')">
                            <i class="bi bi-download"></i> 下载
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// 添加全局错误处理
window.onerror = function(msg, url, line, col, error) {
    console.error('Global error:', error);
    showErrorMessage('发生错误，请刷新页面重试');
    return false;
};

// 添加通用的消息提示函数
function showMessage(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 自动关闭
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// 优化下载函数
async function downloadNovel(novelId) {
    try {
        showProgressModal();
        
        const response = await fetch(`/api/download/${novelId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '下载失败');
        }
        
        showMessage('已添加到下载队列', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showMessage(error.message, 'danger');
        hideProgressModal();
    }
}

// 优化进度模态框管理
const ProgressModal = {
    instance: null,
    
    init() {
        this.instance = new bootstrap.Modal(document.getElementById('progressModal'), {
            backdrop: true,
            keyboard: true
        });
        
        // 绑定事件
        document.getElementById('minimizeProgress').addEventListener('click', () => {
            this.hide();
            document.getElementById('showProgress').classList.remove('d-none');
        });
        
        document.getElementById('showProgress').addEventListener('click', () => {
            this.show();
            document.getElementById('showProgress').classList.add('d-none');
        });
    },
    
    show() {
        if (!this.instance) this.init();
        this.instance.show();
    },
    
    hide() {
        if (this.instance) this.instance.hide();
    },
    
    updateProgress(data) {
        const progressBar = document.querySelector('.progress-bar');
        const currentChapter = document.getElementById('currentChapter');
        
        progressBar.style.width = `${data.percentage}%`;
        progressBar.textContent = `${data.percentage.toFixed(1)}%`;
        
        if (data.chapter) {
            currentChapter.textContent = `当前章节: ${data.chapter}`;
        }
    }
};

// 优化 Socket.IO 初始化
function initializeSocketIO() {
    const socket = io();
    
    socket.on('connect_error', (error) => {
        console.error('Socket.IO connection error:', error);
        showMessage('连接服务器失败，请刷新页面重试', 'danger');
    });
    
    socket.on('progress', (data) => {
        ProgressModal.show();
        ProgressModal.updateProgress(data);
    });
    
    socket.on('log', (data) => {
        const logOutput = document.getElementById('logOutput');
        logOutput.textContent += data.message + '\n';
        logOutput.scrollTop = logOutput.scrollHeight;
    });
    
    socket.on('queue_update', (data) => {
        updateQueueStatus(data);
    });
}

// 优化页面加载
document.addEventListener('DOMContentLoaded', () => {
    // 延迟加载非关键资源
    requestIdleCallback(() => {
        loadSocketIO();
    });
    
    // 默认加载搜索页面
    loadPage('components/search.html');
    
    // 初始化进度模态框
    ProgressModal.init();
});

// 添加键盘快捷键支持
document.addEventListener('keydown', function(e) {
    // Ctrl + Q: 显示/隐藏下载队列
    if (e.ctrlKey && e.key === 'q') {
        e.preventDefault();
        const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (progressModal) {
            if (progressModal._isShown) {
                progressModal.hide();
            } else {
                progressModal.show();
            }
        }
    }
    
    // Esc: 最小化进度窗口
    if (e.key === 'Escape') {
        const progressModal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (progressModal && progressModal._isShown) {
            progressModal.hide();
            document.getElementById('showProgress').classList.remove('d-none');
        }
    }
});

// 添加清理缓存功能
document.getElementById('clearCache').addEventListener('click', function(e) {
    e.preventDefault();
    if (confirm('确定要清理缓存吗？这将删除所有下载的JSON文件，但不会影响已下载的小说文件。')) {
        fetch('/api/clear-cache', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showMessage('缓存已清理', 'success');
                } else {
                    showMessage('清理缓存失败: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('清理缓存失败', 'danger');
            });
    }
});

// 添加消息提示功能
function showMessage(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.getElementById('toast-container').appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}
