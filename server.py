from argparse import ArgumentParser
import os
from pathlib import Path
from pickle import BUILD
import logging
from enum import Enum


FAIL = "\x1b[0;31m[ - ]\x1b[0m asd"
PASS = "\x1b[0;32m[ + ]\x1b[0m asd"


# dirs
EXP_DIR = "/experiments"
BUILD_DIR = os.path.join(EXP_DIR, "build")
ROOT_DIR = os.path.abspath(".")
COMPILE_BC_PATH = os.path.join(ROOT_DIR, "tools", "compile_bc.py")


# servers
LightFTP    = "lightftp"
Live555     = "live555"


class Mode(Enum):
    REMOVE = "remove"
    BUILD  = "build"
    RUN    = "run"
    ERROR = "error"

    @staticmethod
    def get(value: str) -> "Mode":
        if value == "remove":
            return Mode.REMOVE
        if value == "build":
            return Mode.BUILD
        if value == "run":
            return Mode.RUN
        return Mode.ERROR


def create_dir_on_absence(path_str: str):
    path = Path(path_str)
    if not path.exists() or not path.is_dir():
        path.mkdir()


def check_exp_dir():
    create_dir_on_absence(EXP_DIR)
    create_dir_on_absence(BUILD_DIR)


def build_lightftp(source_path: str, bin_path: str, misc_path: str):
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
    os.system(f"CC=gclang CXX=gclang++ CFLAGS=\"-fPIC\" make && mkdir build && cp fftp build/{LightFTP}")

    os.chdir("./build")
    os.system(f"get-bc {LightFTP} && CFLAGS=\"-lpthread -lgnutls -fpie -pie\" python3 {COMPILE_BC_PATH} {LightFTP}.bc")
    create_dir_on_absence(bin_path)
    os.system(f"cp ./* {bin_path}")
    os.system(f"cp -r {misc_path}/* {bin_path}")

    # logging.info(f"{PASS} Build lightftp successfully!")


def run_lightftp(bin_path):
    os.chdir(bin_path)
    os.system("rm -r out && kill -s 9 $(pgrep lightftp.*)")
    os.system(f"fuzzer -i in -o out -c ./targets.json -t ./{LightFTP}.track -s ./{LightFTP}.san.fast -n tcp://127.0.0.1:2200 -- ./{LightFTP}.fast ./fftp.conf 2200")


def build_live555(source_path: str, bin_path: str, misc_path: str):
    pass


def run_live555(bin_path):
    pass


def remove_server(source_path: str, bin_path: str):
    if os.path.exists(source_path):
        os.system(f"rm -r {source_path}")
    if os.path.exists(bin_path):
        os.system(f"rm -r {bin_path}")


HANDLERS = {
    Mode.REMOVE: remove_server,
    Mode.BUILD: {
        LightFTP: build_lightftp,
        Live555: build_live555,
    },
    Mode.RUN: {
        LightFTP: run_lightftp,
        Live555: run_live555,
    }
}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = ArgumentParser(
        prog="Server builder", 
        usage=None, 
        description="To build network protocol server implementations for fuzzing"
    )
    parser.add_argument("mode", choices=[Mode.BUILD.value, Mode.REMOVE.value, Mode.RUN.value])
    parser.add_argument("server_name", choices=[LightFTP, Live555])

    args = parser.parse_args()
    mode: Mode = Mode.get(args.mode)
    server_name: str = args.server_name

    check_exp_dir()

    source_path = os.path.join(BUILD_DIR, server_name)
    bin_path = os.path.join(EXP_DIR, server_name)
    misc_path = os.path.join(ROOT_DIR, "misc", server_name)

    if mode == Mode.BUILD:      # build
        HANDLERS[mode][server_name](source_path, bin_path, misc_path)
    if mode == Mode.REMOVE:     # remove
        HANDLERS[mode](source_path, bin_path)
    if mode == Mode.RUN:        # run
        HANDLERS[mode][server_name](bin_path)
    