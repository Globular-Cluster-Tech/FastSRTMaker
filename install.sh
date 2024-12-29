#!/bin/bash



# 检查xcode是否安装
if ! xcode-select -p; then
    echo "xcode未安装，正在安装...，安装成功后请重新运行安装脚本"
    sudo xcode-select --install
    exit 1
fi


# 下载项目,下载python 3.10，安装poetry，安装项目依赖，安装brew，安装ffmpeg，添加命令到/usr/bin/fastsrtmaker

# 检查并安装 Homebrew
if ! command -v /opt/homebrew/bin/brew &> /dev/null; then
    echo "正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew 已安装"
fi

# 检查当前shell，如果PATH中不包含brew目录，添加PATH到配置文件中

SHELL_COMMAN=$(echo $SHELL | sed 's/.*\///')
if [[ $SHELL_COMMAN == "zsh" ]]; then
    if ! grep -q "/opt/homebrew/bin" ~/.zshrc; then
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
    fi
elif [[ $SHELL_COMMAN == "bash" ]]; then
    if ! grep -q "/opt/homebrew/bin" ~/.bash_profile; then
        echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.bash_profile
    fi
fi

# SHELL配置生效
export PATH="/opt/homebrew/bin:$PATH"

# 安装 ffmpeg
if ! command -v /opt/homebrew/bin/ffmpeg &> /dev/null; then
    echo "正在安装 ffmpeg..."
    brew install ffmpeg 1>>/tmp/fastsrtmaker.log 2>&1
fi



# 安装 Python 3.10
if ! command -v /opt/homebrew/bin/pyenv &> /dev/null; then
    echo "正在安装 pyenv ..."
    brew install pyenv 1>>/tmp/fastsrtmaker.log 2>&1
fi

if ! command -v /opt/homebrew/bin/pyenv-virtualenv &> /dev/null; then
    echo "正在安装 pyenv-virtualenv ..."
    brew install pyenv-virtualenv 1>>/tmp/fastsrtmaker.log 2>&1
fi



# 添加 pyenv 配置到 shell 配置文件

if ! grep -q "pyenv init" ~/."$SHELL_COMMAN"rc; then
    echo 'eval "$(pyenv init --path)"' >> ~/."$SHELL_COMMAN"rc
    echo 'eval "$(pyenv init -)"' >> ~/."$SHELL_COMMAN"rc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/."$SHELL_COMMAN"rc
fi

# SHELL配置生效
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

pyenv global system  &> /dev/null

# 安装 python 3.10
if ! pyenv versions | grep -q "3.10"; then
    pyenv install 3.10 1>>/tmp/fastsrtmaker.log 2>&1
    pyenv virtualenv 3.10 FastSRTMaker 1>>/tmp/fastsrtmaker.log 2>&1

fi
pyenv activate FastSRTMaker 1>>/tmp/fastsrtmaker.log 2>&1


# 安装 poetry
echo "正在安装 Poetry..."
pip install --upgrade pip 1>>/tmp/fastsrtmaker.log 2>&1
pip install -U poetry 1>>/tmp/fastsrtmaker.log 2>&1



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
        git pull 1>>/tmp/fastsrtmaker.log 2>&1
        cd -
    else
        echo "错误: $TMP_DIR 目录已存在，但不是git仓库。"
        echo "请删除该目录后重新运行安装脚本。"
        exit 1
    fi
else
    git clone https://github.com/yaule/FastSRTMaker.git -b dev "$TMP_DIR"
fi

cd "$TMP_DIR"

# 使用 Poetry 安装依赖
echo "正在安装项目依赖..."
poetry install 1>>/tmp/fastsrtmaker.log 2>&1

# 创建启动脚本
echo "正在创建启动脚本..."

if [ ! -d /usr/local/bin ]; then
    sudo mkdir -p /usr/local/bin
fi



sudo tee /usr/local/bin/fastsrtmaker <<EOF
#!/bin/zsh
source ~/.$(echo $SHELL_COMMAN)rc 1>>/dev/null 2>&1
cd "$TMP_DIR/"
pyenv activate FastSRTMaker 1>>/dev/null 2>&1

GIT_OUTPUT=\$(git pull)

if [[ "\$GIT_OUTPUT" != 'Already up to date.' ]]; then
    poetry install 1>>/dev/null 2>&1
fi

poetry shell 1>>/dev/null 2>&1

python3.10 main.py "\$@"

pyenv deactivate 1>>/dev/null 2>&1

EOF

# 添加执行权限
sudo chmod +x /usr/local/bin/fastsrtmaker

echo "安装完成！现在可以使用 fastsrtmaker 命令了。"
