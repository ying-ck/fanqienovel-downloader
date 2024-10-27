# 使用 Python 3.13 作为基础镜像
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY src/ ./src/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/src/data /app/src/novel_downloads

# 设置环境变量
ENV PYTHONPATH=/app
ENV FLASK_APP=src/server.py

# 暴露端口
EXPOSE 12930

# 启动命令
CMD ["python", "src/server.py"]
