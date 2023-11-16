use std::{net::{TcpStream, Shutdown}, io::{Write, Read}, time::Duration};

use angora_common::config;

use super::{HostAddr, connection::Connection};

pub struct Server<'a> {
    addr: &'a HostAddr,
    delay: u64,
    server_name: &'a str,
    server_pid: u32,
    conn: Option<Connection>,
}

impl<'a> Server<'a> {

    pub fn new(addr: &'a HostAddr, server_name: &'a str, server_pid: u32) -> Self {
        Self {
            addr, 
            delay: config::SERVER_CONNECTION_DELAY, 
            server_name,
            server_pid, 
            conn: None
        }
    }

    /// Connect to the server
    pub fn connect(&mut self) -> Result<(), std::io::Error> {
        std::thread::sleep(std::time::Duration::from_millis(self.delay));
        match self.addr {
            HostAddr::TCP(addr) => {
                let socket = TcpStream::connect(addr)?;
                socket.set_read_timeout(Some(Duration::new(1, 0))).unwrap();
                debug!("Connect to {} ({}) successfully!", addr, self.server_pid);
                self.conn = Some(Connection::TCP(socket));
                Ok(())
            },
            HostAddr::UDP(addr) => {
                unimplemented!()
            }
        }
    }

    /// Execute the testcase
    pub fn execute(&mut self, input: &[u8]) -> Result<(), std::io::Error> {
        let mut recv_buf = vec![0; config::RECV_BUF_SIZE];
        let mut recved_msg: Vec<u8> = Vec::new();
        match &mut self.conn {
            Some(Connection::TCP(ref mut socket)) => {
                // send messages to the server
                let writed_size = socket.write(input)?;
                debug!("Write {} bytes to {}.", writed_size, self.addr);

                // receive messages from the server
                let mut size = socket.read(&mut recv_buf)?;
                while size == recv_buf.len() {
                    recved_msg.extend(&recv_buf[..size]);
                    recv_buf.clear();
                    size = socket.read(&mut recv_buf).unwrap();
                }
                recved_msg.extend(&recv_buf[..size]);
                debug!("Recv {} bytes from {}: \n{}", recved_msg.len(), self.addr, String::from_utf8_lossy(&recved_msg));
                
                Ok(())
            },
            Some(Connection::UDP(ref mut socket)) => {
                unimplemented!()
            },
            None => unreachable!(),
        }
    }

    pub fn shutdown(&mut self) -> Result<(), std::io::Error> {
        self.conn = match &self.conn {
            Some(Connection::TCP(socket)) => {
                socket.shutdown(Shutdown::Both)?;
                None
            },
            _ => None,
        };
        Ok(())
    }
}