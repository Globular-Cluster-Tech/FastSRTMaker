#!/bin/bash


# 下载项目,下载python 3.10，安装poetry，安装项目依赖，安装brew，安装ffmpeg，添加命令到/usr/bin/fastsrtmaker

# 检查并安装 Homebrew
if ! command -v brew &> /dev/null; then
    echo "正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew 已安装"
fi

# 安装 Python 3.10
echo "正在安装 Python 3.10..."
brew install python@3.10

# 安装 ffmpeg
echo "正在安装 ffmpeg..."
brew install ffmpeg

# 安装 poetry
echo "正在安装 Poetry..."
python3.10 -m pip install --upgrade pip
python3.10 -m pip install poetry

# 创建临时目录并克隆项目
# 检查并创建临时目录
TMP_DIR="$HOME/Library/fastsrtmaker"

# 检查目录是否存在
if [ -d "$TMP_DIR" ]; then
    # 检查是否为当前项目的git仓库
    if [ -d "$TMP_DIR/.git" ]; then
        cd "$TMP_DIR"
        REMOTE_URL=$(git config --get remote.origin.url)
        if [ "$REMOTE_URL" != "https://github.com/yaule/FastSRTMaker.git" ]; then
            echo "错误: $TMP_DIR 目录已存在，但不是当前项目。"
            echo "请删除该目录后重新运行安装脚本。"
            exit 1
        fi
        echo "项目目录已存在且为当前项目，继续安装..."
        cd -
    else
        echo "错误: $TMP_DIR 目录已存在，但不是git仓库。"
        echo "请删除该目录后重新运行安装脚本。"
        exit 1
    fi
else
    git clone https://github.com/yaule/FastSRTMaker.git  "$TMP_DIR"
fi

cd "$TMP_DIR"





# 使用 Poetry 安装依赖
echo "正在安装项目依赖..."
poetry install

# 创建启动脚本
cat > /usr/local/bin/fastsrtmaker << 'EOF'
#!/bin/bash
cd "$TMP_DIR/FastSRTMaker"
poetry run python main.py "$@"
EOF

# 添加执行权限
chmod +x /usr/local/bin/fastsrtmaker

echo "安装完成！现在可以使用 fastsrtmaker 命令了。"
