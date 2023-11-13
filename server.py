from argparse import ArgumentParser
import os
from pathlib import Path
from pickle import BUILD


FAIL = "\x1b[0;31m[-]\x1b[0m asd"
PASS = "\x1b[0;32m[-]\x1b[0m asd"

EXP_DIR = "/experiments"
BUILD_DIR = os.path.join(EXP_DIR, "build")
ROOT_DIR = os.path.abspath(".")
COMPILE_BC_PATH = os.path.join(ROOT_DIR, "tools", "compile_bc.py")


def create_dir_on_absence(path_str: str):
    path = Path(path_str)
    if not path.exists() or not path.is_dir():
        path.mkdir()


def check_exp_dir():
    create_dir_on_absence(EXP_DIR)
    create_dir_on_absence(BUILD_DIR)


def build_lightftp(source_path: str, bin_path: str):
    if os.system("apt install -y gnutls-dev build-essential") != 0:
        print(f"{FAIL} Failed to install dependencies of lightftp, now try with sudo")
        if os.system("sudo apt install -y gnutls-dev build-essential") != 0:
            print(f"{FAIL} Failed to install dependencies of lightftp with sudo, exit")
            exit(-1)

    os.chdir(BUILD_DIR)
    os.system(f"git clone https://github.com/hfiref0x/LightFTP.git {source_path}")

    os.chdir(source_path)
    os.system("git checkout 5980ea1")
    os.system("wget https://github.com/profuzzbench/profuzzbench/raw/master/subjects/FTP/LightFTP/fuzzing.patch")
    os.system("patch -p1 < fuzzing.patch")

    os.chdir("./Source/Release")
    os.system("make clean && rm -r build")
    os.system("CC=gclang CXX=gclang++ CFLAGS=\"-fPIC\" make && mkdir build && cp fftp build")

    os.chdir("./build")
    os.system(f"get-bc fftp && CFLAGS=\"-lpthread -lgnutls -fpie -pie\" python3 {COMPILE_BC_PATH} fftp.bc")
    create_dir_on_absence(bin_path)
    os.system(f"cp ./* {bin_path}")

    print(f"{PASS} Build lightftp successfully!")


def build_live555():
    pass


def remove_server(source_path, bin_path):
    if os.path.exists(source_path):
        os.system(f"rm -r {source_path}")
    if os.path.exists(bin_path):
        os.system(f"rm -r {bin_path}")


HANDLERS = {
    0: remove_server,
    1: {
        "lightftp": build_lightftp,
        "live555": build_live555,
    }
}


if __name__ == "__main__":
    
    parser = ArgumentParser(
        prog="Server builder", 
        usage=None, 
        description="To build network protocol server implementations for fuzzing"
    )
    parser.add_argument("mode", choices=["build", "remove"])
    parser.add_argument("server_name", choices=["lightftp", "live555"])

    args = parser.parse_args()
    is_build: int = 1 if args.mode == "build" else 0  
    server_name: str = args.server_name

    check_exp_dir()

    source_path = os.path.join(BUILD_DIR, server_name)
    bin_path = os.path.join(EXP_DIR, server_name)

    HANDLERS[is_build][server_name](source_path, bin_path)
    