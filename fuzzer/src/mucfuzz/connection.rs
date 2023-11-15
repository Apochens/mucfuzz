use std::{net::{TcpStream, UdpSocket}, fmt::{Debug, Display}};

#[derive(Clone)]
pub enum AddrType {
    TCP(String),
    UDP(String),
}

impl AddrType {
    pub fn copy(&self) -> AddrType {
        match self {
            AddrType::TCP(addr) => AddrType::TCP(addr.to_string()),
            AddrType::UDP(addr) => AddrType::UDP(addr.to_string()),
        }
    }
}

impl Debug for AddrType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TCP(addr) => write!(f, "tcp://{}", addr),
            Self::UDP(addr) => write!(f, "udp://{}", addr),
        }
    }
}

impl Display for AddrType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TCP(addr) => write!(f, "tcp://{}", addr),
            Self::UDP(addr) => write!(f, "udp://{}", addr),
        }
    }
}


#[derive(Debug)]
pub enum Connection {
    TCP(TcpStream),
    UDP(UdpSocket),
}

