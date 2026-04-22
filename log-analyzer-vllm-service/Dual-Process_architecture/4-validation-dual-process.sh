#!/bin/sh
# 4-validation-dual-process.sh
# 验证双进程架构功能

echo "Testing Dual Process Architecture..."
echo ""

# 测试 1: 健康检查
echo "[Test 1] Health Check..."
curl -s http://localhost:8000/health | jq
echo ""

# 测试 2：成功案例
echo "[Test 2] Successful Transcoding Log..."
curl -X POST \
   -d "ffmpeg version N-random-g73a871f3b25 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_63.mp4':\n  Duration: 00:00:09.00, start: 0.000000, bitrate: 1000 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 26 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x8a927a4d530184e9] PSNR Y:42.50 U:42.63 V:40.40 Avg:42.00 Global:31.90\nOutput #0, mp4, to 'output_video_93.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  234 fps= 26 q=29.0 size=     22527kB time=00:00:09.00 bitrate=1956kbits/s speed=2.5x\nvideo:20274kB audio:2252kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000% " \
   http://localhost:8000/analyze | jq
echo ""


# 测试 3： 失败案例
echo "[Test 3] Failed Transcoding Log..."
curl -X POST \
    -d "ffmpeg version N-random-g1032338ff91 shared. Build: gcc-latest.\nconfiguration: --enable-gpl --enable-libx264 --enable-libx265\nlibavutil      56. 46.100 / 56. 46.100\nlibavcodec     58. 92.100 / 58. 92.100\nlibavformat    58. 46.100 / 58. 46.100\nError while opening encoder for output stream #0:0 - maybe incorrect parameters such as codec tags, or the codec was not enabled in FFmpeg." \
    http://localhost:8000/analyze | jq
echo ""

echo "All tests completed!"