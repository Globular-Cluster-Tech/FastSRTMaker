# FastSRTMaker

在macOS里快速生成字幕文件，免费离线生成，可以翻译成多种语言

# 使用说明文档

## 项目概述
该项目旨在从视频文件中提取音频，并生成相应的字幕文件，包括简体中文、繁体中文和英文字幕。项目使用了 argostranslate 库中的翻译模型来实现英文翻译，并使用 OpenCC 库进行简体到繁体的转换。

# 安装和使用

## 安装xcode

```sh
sudo xcode-select --install
```

## 安装

在命令行中运行以下命令安装：
```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Globular-Cluster-Tech/FastSRTMaker/refs/heads/dev/install.sh)"
```



## 使用方法
```sh
fastsrtmaker <video_path>
```
生成的音视频内容字幕文件在视频目录下

```sh
fastsrtmaker <srt_path>
```
将字幕文件翻译成默认的几种语言，翻译后的字幕文件在相同目录下


## 卸载

```sh
bash -c "$(curl -fsSL https://raw.githubusercontent.com/Globular-Cluster-Tech/FastSRTMaker/refs/heads/dev/uninstall.sh)"
```


# 贡献

欢迎任何形式的贡献！请提交问题或拉取请求以帮助改进项目。

# 许可证

本项目采用 GNUv3 许可证，详细信息请查看 LICENSE 文件。
