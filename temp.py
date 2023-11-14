# ./fuzzer -c ./targets.json -i in -o out -t ./fftp.track -s ./fftp.san.fast -n tcp://127.0.0.1:2200  -- ./fftp.fast ./fftp.conf
# cp /home/linuxbrew/rustproj/mucfuzzer/target/debug/fuzzer .

from pwn import socket

socket = socket.socket()
socket.connect(("127.0.0.1", 8554))

msg = "\r\n".join([
    "DESCRIBE rtsp://127.0.0.1:8554/aacAudioTest RTSP/1.0\r\nCSeq: 2\r\nUser-Agent: ./testRTSPClient (LIVE555 Streaming Media v2018.08.28)\r\nAccept: application/sdp\r\n",
    "SETUP rtsp://127.0.0.1:8554/aacAudioTest/track1 RTSP/1.0\r\nCSeq: 3\r\nUser-Agent: ./testRTSPClient (LIVE555 Streaming Media v2018.08.28)\r\nTransport: RTP/AVP;unicast;client_port=38784-38785\r\n",
    "PLAY rtsp://127.0.0.1:8554/aacAudioTest/ RTSP/1.0\r\nCSeq: 4\r\nUser-Agent: ./testRTSPClient (LIVE555 Streaming Media v2018.08.28)\r\nSession: 000022B8\r\nRange: npt=0.000-\r\n",
])

socket.send(msg.encode())

rec = socket.recv(2000)
print(rec)
