from ..utils import sanitize_filename

def index(title: str,chapters: dict[str, str]) -> str:
    """Create HTML index page with CSS styling"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 目录</title>
    <style>
        :root {{
            --bg-color: #f5f5f5;
            --text-color: #333;
            --link-color: #007bff;
            --hover-color: #0056b3;
        }}
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #222;
                --text-color: #fff;
                --link-color: #66b0ff;
                --hover-color: #99ccff;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .toc {{
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }}
        .toc a {{
            color: var(--link-color);
            text-decoration: none;
            display: block;
            padding: 8px 0;
            transition: all 0.2s;
        }}
        .toc a:hover {{
            color: var(--hover-color);
            transform: translateX(10px);
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="toc">
        {''.join(f'<a href="{sanitize_filename(title)}.html">{title}</a>' for title in chapters.keys())}
    </div>
</body>
</html>
"""

def content(title: str,content: str,prev_link: str,next_link: str,config) -> str:
    f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        /* ... Same CSS variables as index ... */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.8;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-color);
            color: var(--text-color);
            max-width: 800px;
            margin: 0 auto;
        }}
        .navigation {{
            display: flex;
            justify-content: space-between;
            padding: 20px 0;
            position: sticky;
            top: 0;
            background-color: var(--bg-color);
        }}
        .navigation a {{
            color: var(--link-color);
            text-decoration: none;
            padding: 8px 16px;
            border: 1px solid var(--link-color);
            border-radius: 4px;
        }}
        .content {{
            text-indent: 2em;
            margin-bottom: 40px;
        }}
    </style>
</head>
<body>
    <div class="navigation">
        <a href="index.html">目录</a>
        {prev_link}
        {next_link}
    </div>
    <h1>{title}</h1>
    <div class="content">
        {content.replace(chr(10), '<br>' + config.kgf * config.kg)}
    </div>
    <div class="navigation">
        <a href="index.html">目录</a>
        {prev_link}
        {next_link}
    </div>
</body>
</html>
"""