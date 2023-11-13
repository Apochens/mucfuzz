# ./fuzzer -c ./targets.json -i in -o out -t ./fftp.track -s ./fftp.san.fast -n tcp://127.0.0.1:2200  -- ./fftp.fast ./fftp.conf
# cp /home/linuxbrew/rustproj/mucfuzzer/target/debug/fuzzer .

from os import system


if system("sudo") != 0:
    print("\x1b[0;31m[-]\x1b[0m asd")
    print("\x1b[0;32m[-]\x1b[0m asd")
    exit(0)


a = 1
a += 1
print(a)