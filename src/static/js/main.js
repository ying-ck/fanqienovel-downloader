// Initialize Socket.IO
const socket = io();

// UI Elements
const content = document.getElementById('content');
const progressModal = new bootstrap.Modal(document.getElementById('progressModal'));
const progressBar = document.querySelector('.progress-bar');
const currentChapter = document.getElementById('currentChapter');
const logOutput = document.getElementById('logOutput');

// Socket.IO Event Handlers
socket.on('progress', (data) => {
    // Update progress bar width
    progressBar.style.width = `${data.percentage}%`;
    progressBar.setAttribute('aria-valuenow', data.percentage);
    
    // Update progress bar text
    progressBar.textContent = data.text || `${Math.round(data.percentage)}%`;
    
    // Update chapter info if available
    if (data.chapter) {
        currentChapter.textContent = `当前章节: ${data.chapter}`;
    }
    
    // If download is complete (100%)
    if (data.percentage === 100) {
        setTimeout(() => {
            logOutput.textContent += '下载完成！\n';
            if (downloadQueue.length > 0) {
                logOutput.textContent += `队列中还有 ${downloadQueue.length} 本小说等待下载...\n`;
            }
        }, 1000);
    }
});

socket.on('log', (data) => {
    logOutput.textContent += data.message + '\n';
    logOutput.scrollTop = logOutput.scrollHeight;
});

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', async (e) => {
        e.preventDefault();
        const page = e.target.dataset.page;
        const response = await fetch(`/templates/components/${page}.html`);
        content.innerHTML = await response.text();
        initializePage(page);
    });
});

// Page Initialization
function initializePage(page) {
    switch (page) {
        case 'search':
            initializeSearch();
            break;
        case 'library':
            loadLibrary();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// Search Functionality
function initializeSearch() {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const directInput = document.getElementById('directInput');
    const directDownloadBtn = document.getElementById('directDownloadBtn');

    // Add direct download handler
    directDownloadBtn.addEventListener('click', async () => {
        const input = directInput.value.trim();
        if (!input) {
            alert('请输入小说ID或链接');
            return;
        }
        await downloadNovel(input);
    });

    // Add search handler
    searchBtn.addEventListener('click', async () => {
        const keyword = searchInput.value.trim();
        if (!keyword) {
            alert('请输入搜索关键词');
            return;
        }

        try {
            const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword)}`);
            const results = await response.json();
            
            if (!results || results.length === 0) {
                searchResults.innerHTML = '<div class="col-12"><div class="alert alert-info">没有找到相关书籍</div></div>';
                return;
            }
            
            searchResults.innerHTML = results.map(book => `
                <div class="col-md-6 mb-3">
                    <div class="card search-result">
                        <div class="card-body">
                            <h5 class="card-title">${book.book_data[0].book_name}</h5>
                            <p class="card-text">作者: ${book.book_data[0].author}</p>
                            <p class="card-text">字数: ${book.book_data[0].word_number}</p>
                            <button class="btn btn-primary download-btn" 
                                    data-id="${book.book_data[0].book_id}">
                                下载
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');

            // Add download handlers
            document.querySelectorAll('.download-btn').forEach(btn => {
                btn.addEventListener('click', async (e) => {
                    const novelId = e.target.dataset.id;
                    await downloadNovel(novelId);
                });
            });
        } catch (error) {
            searchResults.innerHTML = '<div class="col-12"><div class="alert alert-danger">搜索失败，请重试</div></div>';
        }
    });

    // Add keyboard event listeners
    directInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            directDownloadBtn.click();
        }
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBtn.click();
        }
    });
}

// Library Functionality
async function loadLibrary() {
    const response = await fetch('/api/novels');
    const novels = await response.json();
    
    const novelList = document.getElementById('novelList');
    novelList.innerHTML = novels.map(novel => `
        <div class="col-md-4 mb-3">
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${novel.name}</h5>
                    <div class="btn-group">
                        ${novel.txt_path ? `
                            <a href="/download/${encodeURIComponent(novel.name)}.txt" 
                               class="btn btn-sm btn-outline-primary">TXT</a>
                        ` : ''}
                        ${novel.epub_path ? `
                            <a href="/download/${encodeURIComponent(novel.name)}.epub" 
                               class="btn btn-sm btn-outline-primary">EPUB</a>
                        ` : ''}
                        ${novel.html_path ? `
                            <a href="/download/${encodeURIComponent(novel.name)}(html).zip" 
                               class="btn btn-sm btn-outline-primary">HTML</a>
                        ` : ''}
                        ${novel.latex_path ? `
                            <a href="/download/${encodeURIComponent(novel.name)}.tex" 
                               class="btn btn-sm btn-outline-primary">LaTeX</a>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

// Settings Functionality
async function loadSettings() {
    const response = await fetch('/api/settings');
    const settings = await response.json();
    
    document.getElementById('kgf').value = settings.kgf;
    document.getElementById('kg').value = settings.kg;
    document.getElementById('delayMin').value = settings.delay[0];
    document.getElementById('delayMax').value = settings.delay[1];
    document.getElementById('saveMode').value = settings.save_mode;
    document.getElementById('xc').value = settings.xc;

    document.getElementById('settingsForm').addEventListener('submit', async (e) => {
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

        await saveSettings(formData);
    });
}

// Add download queue management
let isDownloading = false;
const downloadQueue = [];

async function processDownloadQueue() {
    if (isDownloading || downloadQueue.length === 0) return;
    
    isDownloading = true;
    const novelId = downloadQueue.shift();
    
    try {
        showProgressBtn.style.display = 'none';
        progressModal.show();
        const response = await fetch(`/api/download/${novelId}`);
        if (!response.ok) {
            throw new Error('Download failed');
        }
        logOutput.textContent = '开始下载...\n';
        
        // Wait for download to complete via socket events
        await new Promise((resolve) => {
            const completeHandler = (data) => {
                if (data.percentage === 100) {
                    socket.off('progress', completeHandler);
                    setTimeout(resolve, 1000);  // Wait a bit after completion
                }
            };
            socket.on('progress', completeHandler);
        });
        
    } catch (error) {
        alert('下载失败，请重试');
    } finally {
        isDownloading = false;
        // Process next download if any
        processDownloadQueue();
    }
}

async function downloadNovel(novelId) {
    if (isDownloading) {
        const choice = confirm('已有小说正在下载中。是否将此小说加入下载队列？');
        if (choice) {
            downloadQueue.push(novelId);
            alert('已加入下载队列，将在当前下载完成后自动开始');
        }
        return;
    }
    
    downloadQueue.push(novelId);
    processDownloadQueue();
}

// Add error handling for settings
async function saveSettings(formData) {
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save settings');
        }
        
        alert('设置已保存');
    } catch (error) {
        alert('保存设置失败，请重试');
    }
}

// Initialize the search page by default
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('[data-page="search"]').click();
});

// Progress Modal Controls
const showProgressBtn = document.getElementById('showProgress');
const minimizeProgressBtn = document.getElementById('minimizeProgress');

minimizeProgressBtn.addEventListener('click', () => {
    progressModal.hide();
    showProgressBtn.style.display = 'block';
});

showProgressBtn.addEventListener('click', () => {
    progressModal.show();
    showProgressBtn.style.display = 'none';
});

// Update socket event handler to manage download state
socket.on('progress', (data) => {
    // Update progress bar width
    progressBar.style.width = `${data.percentage}%`;
    progressBar.setAttribute('aria-valuenow', data.percentage);
    
    // Update progress bar text
    progressBar.textContent = data.text || `${Math.round(data.percentage)}%`;
    
    // Update chapter info if available
    if (data.chapter) {
        currentChapter.textContent = `当前章节: ${data.chapter}`;
    }
    
    // If download is complete (100%)
    if (data.percentage === 100) {
        setTimeout(() => {
            logOutput.textContent += '下载完成！\n';
            if (downloadQueue.length > 0) {
                logOutput.textContent += `队列中还有 ${downloadQueue.length} 本小说等待下载...\n`;
            }
        }, 1000);
    }
});

// Update progress modal to show queue status
function updateProgressModalTitle() {
    const modalTitle = document.querySelector('.modal-title');
    if (downloadQueue.length > 0) {
        modalTitle.textContent = `下载进度 (队列中: ${downloadQueue.length})`;
    } else {
        modalTitle.textContent = '下载进度';
    }
}

// Add queue status to the progress modal
const modalBody = document.querySelector('.modal-body');
const queueStatus = document.createElement('div');
queueStatus.className = 'queue-status mt-2';
modalBody.insertBefore(queueStatus, modalBody.firstChild);

function updateQueueStatus() {
    queueStatus.textContent = downloadQueue.length > 0 
        ? `下载队列中还有 ${downloadQueue.length} 本小说` 
        : '';
}

// Update the queue status whenever it changes
const originalPush = downloadQueue.push;
downloadQueue.push = function(...args) {
    const result = originalPush.apply(this, args);
    updateQueueStatus();
    updateProgressModalTitle();
    return result;
};

const originalShift = downloadQueue.shift;
downloadQueue.shift = function() {
    const result = originalShift.apply(this);
    updateQueueStatus();
    updateProgressModalTitle();
    return result;
};
