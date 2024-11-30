#!/bin/bash

# 删除项目目录
rm -rf ~/Library/fastsrtmaker

# 删除命令
rm -f /usr/bin/fastsrtmaker

# 删除poetry环境
rm -rf ~/Library/Caches/pypoetry

# 删除python 3.10
brew uninstall python@3.10

# 删除ffmpeg
brew uninstall ffmpeg

# 删除homebrew
brew uninstall --zap homebrew




echo "卸载完成！"

