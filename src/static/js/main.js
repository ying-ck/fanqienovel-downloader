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
                if (novelId) {
                    // 使用 loadPage 而不是直接改变 location
                    loadPage(`components/reader.html?novel_id=${novelId}`);
                    
                    // 更新 URL，但不刷新页面
                    window.history.pushState(
                        { novelId: novelId }, 
                        '', 
                        `/components/reader.html?novel_id=${novelId}`
                    );
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

// 初始化各个页面的功能
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
                        // 处理搜索结果
                        displaySearchResults(data);
                    })
                    .catch(error => console.error('Error:', error));
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
                        <div class="card">
                            <div class="card-body">
                                <h5 class="card-title">${novel.name}</h5>
                                <p class="card-text">
                                    状态: ${novel.status || '未知'}<br>
                                    最后更新: ${novel.last_updated || '未知'}
                                </p>
                                <button class="btn btn-primary btn-sm" 
                                        onclick="loadPage('components/reader.html?novel_id=${novel.novel_id}')">
                                    阅读
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
            }
        })
        .catch(error => console.error('Error:', error));
}

function displaySearchResults(results) {
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = results.map(result => `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">${result.book_data[0].book_name}</h5>
                        <p class="card-text">
                            作者: ${result.book_data[0].author}<br>
                            字数: ${result.book_data[0].word_number}
                        </p>
                        <button class="btn btn-primary btn-sm" 
                                onclick="downloadNovel('${result.book_data[0].book_id}')">
                            下载
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

function downloadNovel(novelId) {
    fetch(`/api/download/${novelId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'queued') {
                alert('小说已添加到下载队列');
            }
        })
        .catch(error => console.error('Error:', error));
}
