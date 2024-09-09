def get_toc_content(chapter: dict[str,str]) -> str:
    toc_content="""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>目录</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                background-color: #f5f5f5;
            }
            h1 {
                color: #333;
                text-align: center;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li a {
                color: #007bff;
                text-decoration: none;
            }
            li a:hover {
                text-decoration: underline;
            }
            p {
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
    <h1>目录</h1>
    <ul>
    """
    for title in chapter:
        toc_content+=f"<li><a href='{title}.html'>{title}</a></li>"
    toc_content+="</ul></body></html>"
    return toc_content


def get_chapter_htmlcontent(title: str,chapter_content: str,chapter: dict[str,str]) -> str:
    formatted_content=chapter_content.replace('\n','<br/>')
    next_chapter_button=""
    if len(chapter)>list(chapter.keys()).index(title)+1:
        next_chapter_key=list(chapter.keys())[list(chapter.keys()).index(title)+1]
        next_chapter_button=f"<button onclick=\"location.href='{next_chapter_key}.html'\">下一章</button>"
    return f"""
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            display: flex;
            min-height: 100vh;
        }}
     .left-side {{
            flex: 1;
            background-color: #ffffff;
        }}
     .content {{
            flex: 3;
            background-color: white;
            padding: 20px;
        }}
     .right-side {{
            flex: 1;
            background-color: #ffffff;
        }}
        button {{
            background-color: #d3d3d3;
            color: black;
            border: none;
            padding: 10px 20px;
            cursor: pointer;
        }}
        #toggle-mode {{
            position: absolute;
            top: 20px;
            right: 20px;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #333;
            }}
         .left-side,.right-side {{
                background-color: #444;
            }}
         .content {{
                background-color: #222;
                color: white;
            }}
            button {{
                background-color: #555;
                color: white;
            }}
        }}
    </style>
    <script>
        let isDarkMode = false;
        document.getElementById('toggle-mode').addEventListener('click', function() {{
            isDarkMode =!isDarkMode;
            if (isDarkMode) {{
                document.body.classList.add('dark-mode');
                localStorage.setItem('mode', 'dark');
            }} else {{
                document.body.classList.remove('dark-mode');
                localStorage.setItem('mode', 'light');
            }}
        }});

        // 检查本地存储以确定初始模式
        const savedMode = localStorage.getItem('mode');
        if (savedMode === 'dark') {{
            document.body.classList.add('dark-mode');
            isDarkMode = true;
        }}
    </script>
</head>
<body>
<div class="left-side"></div>
<div class="content">
    <h1>{title}</h1>
    <p>{formatted_content}</p>
    <a href="#" id="back-to-top">返回顶部</a>
</div>
<div class="right-side"></div>
<div style="text-align: center; position: fixed; bottom: 20px; width: 100%;">
    <button onclick="location.href='index.html'">目录</button>
    {next_chapter_button}
    <button onclick="backToTop()">返回顶部</button>
    <button id="toggle-mode">切换模式</button>
</div>
<script>
    // 当用户滚动页面时显示/隐藏返回顶部按钮
    window.onscroll = function() {{
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {{
            document.getElementById("back-to-top").style.display = "block";
        }} else {{
            document.getElementById("back-to-top").style.display = "none";
        }}
    }};

    // 当用户点击返回顶部按钮时，滚动页面到顶部
    function backToTop() {{
        document.body.scrollTop = 0;
        document.documentElement.scrollTop = 0;
    }}
</script>
</body>
</html>
"""
