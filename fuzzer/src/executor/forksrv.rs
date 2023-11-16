use crate::mucfuzz::HostAddr;

use super::{limit::SetLimit, *};
use angora_common::defs::*;
use byteorder::{LittleEndian, ReadBytesExt};
use libc;
use std::{
    collections::HashMap,
    fs::{self, File},
    io::prelude::*,
    os::unix::{
        io::RawFd,
        net::{UnixListener, UnixStream},
    },
    path::{Path, PathBuf},
    process::{Command, Stdio},
    time::Duration, net::{TcpStream, UdpSocket},
};

// Just meaningless value for forking a new child
static FORKSRV_NEW_CHILD: [u8; 4] = [8, 8, 8, 8];

#[derive(Debug)]
pub struct Forksrv {
    path: String,
    pub socket: UnixStream,
    uses_asan: bool,
    is_stdin: bool,

    /* mucfuzzer */
    hostaddr: Option<HostAddr>,
    input_path: String,
}

impl Forksrv {
    pub fn new(
        socket_path: &str,
        target: &(String, Vec<String>),
        envs: &HashMap<String, String>,
        fd: RawFd,
        is_stdin: bool,
        uses_asan: bool,
        time_limit: u64,
        mem_limit: u64,
        
        /* mucfuzzer */
        hostaddr: Option<HostAddr>,
        input_path: &str,
    ) -> Forksrv {
        debug!("socket_path: {:?}", socket_path);
        let listener = match UnixListener::bind(socket_path) {
            Ok(sock) => sock,
            Err(e) => {
                error!("FATAL: Failed to bind to socket: {:?}", e);
                panic!();
            }
        };

        let mut envs_fk = envs.clone();
        envs_fk.insert(ENABLE_FORKSRV.to_string(), String::from("TRUE"));
        envs_fk.insert(FORKSRV_SOCKET_PATH_VAR.to_string(), socket_path.to_owned());
        match Command::new(&target.0)
            .args(&target.1)
            .stdin(Stdio::null())
            .envs(&envs_fk)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .mem_limit(mem_limit.clone())
            .setsid()
            .pipe_stdin(fd, is_stdin)
            .spawn()
        {
            Ok(_) => (),
            Err(e) => {
                error!("FATAL: Failed to spawn child. Reason: {}", e);
                panic!();
            }
        };

        // FIXME: block here if client doesn't exist.
        let (socket, _) = match listener.accept() {
            Ok(a) => a,
            Err(e) => {
                error!("FATAL: failed to accept from socket: {:?}", e);
                panic!();
            }
        };

        socket
            .set_read_timeout(Some(Duration::from_secs(time_limit)))
            .expect("Couldn't set read timeout");
        socket
            .set_write_timeout(Some(Duration::from_secs(time_limit)))
            .expect("Couldn't set write timeout");

        debug!("All right -- Init ForkServer {} successfully!", socket_path);

        Forksrv {
            path: socket_path.to_owned(),
            socket,
            uses_asan,
            is_stdin,
            hostaddr,
            input_path: input_path.to_owned(),
        }
    }

    pub fn run(&mut self) -> StatusType {
        if self.socket.write(&FORKSRV_NEW_CHILD).is_err() {
            warn!("Fail to write socket!!");
            return StatusType::Error;
        }

        let mut buf = vec![0; 4];
        let child_pid: i32;
        match self.socket.read(&mut buf) {
            Ok(_) => {
                child_pid = match (&buf[..]).read_i32::<LittleEndian>() {
                    Ok(a) => a,
                    Err(e) => {
                        warn!("Unable to recover child pid: {:?}", e);
                        return StatusType::Error;
                    }
                };
                if child_pid <= 0 {
                    warn!(
                        "Unable to request new process from frok server! {}",
                        child_pid
                    );
                    return StatusType::Error;
                }
            }
            Err(error) => {
                warn!("Fail to read child_id -- {}", error);
                return StatusType::Error;
            }
        }

        /* mucfuzz */
        {
            let mut buf = Vec::new();
            match File::open(&self.input_path) {
                Ok(mut f) => {
                    if f.read_to_end(&mut buf).is_err() {
                        panic!("Cannot read {}", &self.input_path);
                    }
                },
                Err(e) => {
                    panic!("Cannot open {} -- {}", &self.input_path, e);
                },
            }

            if let Some(socket_type) = &self.hostaddr {
                match socket_type {
                    HostAddr::TCP(addr) => {
                        std::thread::sleep(std::time::Duration::from_millis(100));
                        let mut socket = TcpStream::connect(addr).expect(&format!("Cannot connect to the host {}", addr));
                        debug!("Connect to {} ({}) successfully!", addr, child_pid);

                        let writed_size = socket.write(&buf).expect("Cannot write to the server");
                        debug!("Write {} bytes to server.", writed_size);

                        let mut recv_buf = Vec::new();
                        let read_size = socket.read(&mut recv_buf).unwrap();
                        debug!("Recv {} bytes: {:?}", read_size, &recv_buf);
                    },
                    HostAddr::UDP(addr) => {
                        let mut socket = UdpSocket::bind("127.0.0.1:8001").expect("Cannot create a UDP socket at 127.0.0.1:8001");
                        socket.connect(addr).expect(&format!("Cannot connect to the host {}", addr));
                        debug!("Connect to {} successfully!", addr);
                    },
                }

            }
        }
        /* mucfuzz */

        buf = vec![0; 4];

        let read_result = self.socket.read(&mut buf);

        match read_result {
            Ok(_) => {
                let status = match (&buf[..]).read_i32::<LittleEndian>() {
                    Ok(a) => a,
                    Err(e) => {
                        warn!("Unable to recover result from child: {}", e);
                        return StatusType::Error;
                    }
                };
                let exit_code = unsafe { libc::WEXITSTATUS(status) };
                let signaled = unsafe { libc::WIFSIGNALED(status) };
                if signaled || (self.uses_asan && exit_code == MSAN_ERROR_CODE) {
                    debug!("Crash code: {}", status);
                    StatusType::Crash
                } else {
                    debug!("Normal exit: {}", status);
                    StatusType::Normal
                }
            }

            Err(_) => {
                debug!("Killing the forked server...");
                unsafe {
                    libc::kill(child_pid, libc::SIGKILL);
                }
                let tmout_buf = &mut [0u8; 16];
                while let Err(_) = self.socket.read(tmout_buf) {
                    warn!("Killing timed out process");
                }
                return StatusType::Timeout;
            }
        }
    }
}

impl Drop for Forksrv {
    fn drop(&mut self) {
        debug!("Exit Forksrv");
        // Tell the child process to exit
        let fin = [0u8; 2];
        if self.socket.write(&fin).is_err() {
            debug!("Fail to write socket !!  FIN ");
        }
        let out = Command::new("pgrep").arg("fftp.fast").output().unwrap();
        println!("forksrv::drop - {:?} ", &String::from_utf8(out.stdout));

        let path = Path::new(&self.path);
        if path.exists() {
            if fs::remove_file(&self.path).is_err() {
                warn!("Fail to remove socket file!!  FIN ");
            }
        }
    }
}
