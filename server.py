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


def install_dependencies(deps: str):
    if os.system(f"apt install -y {deps}") != 0:
        print(f"{FAIL} Failed to install dependencies of lightftp, now try with sudo")
        if os.system(f"sudo apt install -y {deps}") != 0:
            print(f"{FAIL} Failed to install dependencies of lightftp with sudo, exit")
            exit(-1)


def build_lightftp(source_path: str, bin_path: str, misc_path: str, patch_path: str):
    install_dependencies("gnutls-dev build-essential")
    create_dir_on_absence(bin_path)

    os.chdir(BUILD_DIR)
    os.system(f"git clone https://github.com/hfiref0x/LightFTP.git {source_path}")
    if not os.path.exists(source_path):
        print(f"{FAIL} cloning {LightFTP} failed!")

    os.chdir(source_path)
    os.system(f"git checkout 5980ea1 && patch -p1 < {patch_path}")

    os.chdir("./Source/Release")
    os.system("make clean && rm -r build")
    os.system(f"CC=gclang CXX=gclang++ CFLAGS=\"-fPIC\" make && cp fftp {bin_path}/{LightFTP}")

    os.chdir(bin_path)
    os.system(f"get-bc {LightFTP} && CFLAGS=\"-lpthread -lgnutls -fpie -pie -fPIC\" python3 {COMPILE_BC_PATH} C {LightFTP}.bc ./fftp.conf")
    os.system(f"cp -r {misc_path}/* {bin_path}")

    # logging.info(f"{PASS} Build lightftp successfully!")


def run_lightftp(bin_path):
    os.chdir(bin_path)
    if os.path.exists("./out"):
        os.system("rm -r out")
    # os.system("rm -r out && kill -s 9 $(pgrep lightftp.*)")
    os.system(f"RUST_LOG=debug fuzzer -i in -o out -c ./targets.json -t ./{LightFTP}.track -s ./{LightFTP}.san.fast -n tcp://127.0.0.1:2200 -- ./{LightFTP}.fast ./fftp.conf 2200")


def build_live555(source_path: str, bin_path: str, misc_path: str, patch_path: str):
    install_dependencies("libssl-dev build-essential")
    create_dir_on_absence(bin_path)

    os.system(f"git clone https://github.com/rgaufman/live555.git {source_path}")
    if not os.path.exists(source_path):
        print(f"{FAIL} cloning {Live555} failed!")

    os.chdir(source_path)
    os.system(f"git checkout ceeb4f4 && patch -p1 < {patch_path}")
    os.system("./genMakefiles linux && CFLAGS=\"-fPIC\" CXXFLAGS=\"-fPIC\" make -j4")
    os.system(f"cp ./testProgs/testOnDemandRTSPServer {bin_path}/{Live555}")

    os.chdir(bin_path)
    os.system(f"get-bc {Live555} && CXXFLAGS=\"-fpie -pie -fPIC\" python3 {COMPILE_BC_PATH} CPP {Live555}.bc 8554")
    os.system(f"cp -r {misc_path}/* {bin_path}")


def run_live555(bin_path):
    os.chdir(bin_path)
    if os.path.exists("./out"):
        os.system("rm -r out")
    os.system(f"RUST_BACKTRACE=full /mucfuzz/bin/fuzzer -i in -o out -c ./targets.json -t ./{Live555}.track -s ./{Live555}.san.fast -n tcp://127.0.0.1:8554 -- ./{Live555}.fast 8554")


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

    create_dir_on_absence(EXP_DIR)
    create_dir_on_absence(BUILD_DIR)

    source_path = os.path.join(BUILD_DIR, server_name)              # /experiments/<server>
    bin_path = os.path.join(EXP_DIR, server_name)                   # /experiments/build/<server>
    misc_path = os.path.join(ROOT_DIR, "misc", server_name)         # /mucfuzz/misc/<server>
    patch_path = os.path.join(                                      # /mucfuzz/misc/patch/<server>.patch
        ROOT_DIR, "misc", "patchs", f"{server_name}.patch") 
          
    if mode == Mode.BUILD:      # build
        HANDLERS[mode][server_name](source_path, bin_path, misc_path, patch_path)
    if mode == Mode.REMOVE:     # remove
        HANDLERS[mode](source_path, bin_path)
    if mode == Mode.RUN:        # run
        HANDLERS[mode][server_name](bin_path)
    