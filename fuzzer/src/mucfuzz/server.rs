use std::{net::TcpStream, io::{Write, Read}, process::Command};

use angora_common::config;

use super::{AddrType, connection::Connection};

pub struct Server {
    addr: AddrType,
    delay: u64,
    server_pid: u32,
    conn: Option<Connection>,
}

impl Server {

    pub fn new(addr: AddrType, server_pid: u32) -> Self {
        Self {addr, delay: config::SERVER_CONNECTION_DELAY, server_pid, conn: None}
    }

    pub fn connect(&mut self) -> Result<(), std::io::Error> {
        std::thread::sleep(std::time::Duration::from_millis(self.delay));
        match self.addr {
            AddrType::TCP(addr) => {
                let socket = TcpStream::connect(addr)?;
                debug!("Connect to {} ({}) successfully!", addr, self.server_pid);
                self.conn = Some(Connection::TCP(socket));
                Ok(())
            },
            AddrType::UDP(addr) => {
                unimplemented!()
            }
        }
    }

    pub fn execute(&self, input: &[u8]) -> Result<(), std::io::Error> {
        let mut recv_buf = vec![0; config::RECV_BUF_SIZE];
        let mut recved_msg: Vec<u8> = Vec::new();
        match &self.conn {
            Some(Connection::TCP(mut socket)) => {
                // send messages to the server
                let writed_size = socket.write(input)?;
                debug!("Write {} bytes to {}.", writed_size, self.addr);
                
                // receive messages from the server
                let mut size = socket.read(&mut recv_buf)?;
                while size == recv_buf.len() {
                    recved_msg.extend(&recv_buf[..size]);
                    recv_buf = vec![0; config::RECV_BUF_SIZE];
                    size = socket.read(&mut recv_buf).unwrap();
                }
                recved_msg.extend(&recv_buf[..size]);
                debug!("Recv {} bytes from {}: \n{}", recved_msg.len(), self.addr, String::from_utf8(recved_msg.to_vec()).unwrap());
                
                Ok(())
            },
            Some(Connection::UDP(mut socket)) => {
                unimplemented!()
            },
            None => {
                Ok(())
            }
        }
    }

    pub fn shutdown() {
        Command::new("kill").args(["-s", "9", "$(pgrep )"])
    }
}