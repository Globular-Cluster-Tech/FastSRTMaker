# FastSRTMaker

在macOS里快速生成字幕文件，免费离线生成

# 使用说明文档

## 项目概述
该项目旨在从视频文件中提取音频，并生成相应的字幕文件，包括简体中文、繁体中文和英文字幕。项目使用了 transformers 库中的翻译模型来实现英文翻译，并使用 OpenCC 库进行简体到繁体的转换。

# 安装和使用

## 安装

在命令行中运行以下命令安装：
```sh
curl -sL https://raw.githubusercontent.com/yaule/FastSRTMaker/refs/heads/main/install.sh | bash
```





## 使用方法
```sh
fastsrtmaker <video_path>
```
生成的字幕文件在视频目录下，文件名格式如下：
- 简体中文字幕：<video_path>_zh.srt
- 繁体中文字幕：<video_path>_zh_hant.srt
- 英文字幕：<video_path>_en.srt


## 卸载

```sh
curl -sL https://raw.githubusercontent.com/yaule/FastSRTMaker/refs/heads/main/uninstall.sh | bash
```


# 贡献

欢迎任何形式的贡献！请提交问题或拉取请求以帮助改进项目。

# 许可证

本项目采用 GNUv3 许可证，详细信息请查看 LICENSE 文件。
