# ./fuzzer -c ./targets.json -i in -o out -t ./fftp.track -s ./fftp.san.fast -n tcp://127.0.0.1:2200  -- ./fftp.fast ./fftp.conf
# cp /home/linuxbrew/rustproj/mucfuzzer/target/debug/fuzzer .

import socket

sock = socket.socket()
sock.connect(("127.0.0.1", 2200))

sock.send(b"USER ubuntu\r\n\r\nPASS ubuntu\r\n")

sock.close()