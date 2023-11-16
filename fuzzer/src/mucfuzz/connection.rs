use std::{net::{TcpStream, UdpSocket}, fmt::{Debug, Display}};

#[derive(Clone)]
pub enum HostAddr {
    TCP(String),
    UDP(String),
}

impl HostAddr {
    pub fn copy(&self) -> HostAddr {
        match self {
            HostAddr::TCP(addr) => HostAddr::TCP(addr.to_string()),
            HostAddr::UDP(addr) => HostAddr::UDP(addr.to_string()),
        }
    }
}

impl Debug for HostAddr {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::TCP(addr) => write!(f, "tcp://{}", addr),
            Self::UDP(addr) => write!(f, "udp://{}", addr),
        }
    }
}

impl Display for HostAddr {
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

