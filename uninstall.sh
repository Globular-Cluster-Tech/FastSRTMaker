#!/bin/bash

# 删除shell配置

SHELL_COMMAN=$(echo $SHELL | sed 's/.*\///')

sed -i '' '/pyenv/d' ~/."$SHELL_COMMAN"rc
sed -i '' '/\/opt\/homebrew\/bin\:/d' ~/."$SHELL_COMMAN"rc


# 删除项目目录
rm -rf ~/Library/fastsrtmaker

# 删除命令
sudo rm -f /usr/local/bin/fastsrtmaker

# 删除pyenv
rm -rf $(pyenv root)/


# 删除ffmpeg
brew uninstall pyenv pyenv-virtualenv ffmpeg 1>>/tmp/fastsrtmaker.log 2>&1

# 删除homebrew
echo "brew uninstall --zap homebrew && sudo rm -rf /opt/homebrew"

echo "卸载完成！"

