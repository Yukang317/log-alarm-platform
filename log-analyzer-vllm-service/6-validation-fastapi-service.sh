#!/bin/sh
# 两例子，一个成功一个失败 -  验证 FastAPI 服务， 测试：实际业务场景验证

curl -X POST \
    -d "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json. ffmpeg version N-random-g897d21b1b44 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_5.mp4':\n  Duration: 00:00:13.00, start: 0.000000, bitrate: 622 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 52 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x81b53c73796d10f5] PSNR Y:46.39 U:48.91 V:47.38 Avg:47.56 Global:47.74\nOutput #0, mp4, to 'output_video_54.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  676 fps= 37 q=29.0 size=     48003kB time=00:00:13.00 bitrate=2870kbits/s speed=2.1x\nvideo:43202kB audio:4800kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000%" \
    http://127.0.0.1:8000/analyze

curl -X POST \
    -d "Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json. ffmpeg version N-random-g1032338ff91 shared. Build: gcc-latest.\nconfiguration: --enable-gpl --enable-libx264 --enable-libx265\nlibavutil      56. 46.100 / 56. 46.100\nlibavcodec     58. 92.100 / 58. 92.100\nlibavformat    58. 46.100 / 58. 46.100\nError while opening encoder for output stream #0:0 - maybe incorrect parameters such as codec tags, or the codec was not enabled in FFmpeg." \
    http://127.0.0.1:8000/analyze

