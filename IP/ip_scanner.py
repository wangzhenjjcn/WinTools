import sys
import socket
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QTextEdit, QGroupBox, QMessageBox,
                             QProgressBar, QSpinBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QTextCursor, QPalette
import ipaddress
import re
import subprocess

"""
IP端口扫描器
Copyright (c) 2024 wangzhenjjcn@gmail.com
Author: wangzhenjjcn
GitHub: https://github.com/wangzhenjjcn/WinTools
"""

def get_local_ip_and_subnet():
    """获取本地IP地址和子网信息"""
    try:
        # 获取本地主机名
        hostname = socket.gethostname()
        # 获取本地IP地址
        local_ip = socket.gethostbyname(hostname)
        
        # 解析IP地址
        ip_obj = ipaddress.IPv4Address(local_ip)
        
        # 获取子网信息
        # 常见的子网掩码
        common_masks = [24, 16, 8]  # /24, /16, /8
        
        for mask in common_masks:
            try:
                network = ipaddress.IPv4Network(f"{local_ip}/{mask}", strict=False)
                if ip_obj in network:
                    # 计算起始和结束IP
                    start_ip = str(network.network_address + 1)  # 排除网络地址
                    end_ip = str(network.broadcast_address - 1)   # 排除广播地址
                    return local_ip, start_ip, end_ip, mask
            except ValueError:
                continue
        
        # 如果无法确定子网，使用默认的/24子网
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        start_ip = str(network.network_address + 1)
        end_ip = str(network.broadcast_address - 1)
        return local_ip, start_ip, end_ip, 24
        
    except Exception as e:
        # 如果获取失败，返回默认值
        return "192.168.1.1", "192.168.0.1", "192.168.1.255", 24

# 常见端口列表
COMMON_PORTS = [
    20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 123, 135, 137, 138, 139, 143,
    161, 162, 389, 443, 445, 465, 514, 515, 520, 548, 554, 587, 631, 636, 993,
    995, 1080, 1433, 1434, 1521, 1723, 2049, 2181, 3306, 3389, 5432, 5900, 5901,
    5902, 5903, 5904, 5905, 5906, 5907, 5908, 5909, 5910, 5984, 6379, 7077, 8080,
    8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8443, 8444, 8445,
    8446, 8447, 8448, 8449, 8450, 9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007,
    9008, 9009, 9010, 9200, 9300, 11211, 27017, 27018, 27019, 28017, 5000, 5001,
    5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010, 5060, 5061, 5671, 5672,
    5900, 5901, 5902, 5903, 5904, 5905, 5906, 5907, 5908, 5909, 5910, 5984, 6000,
    6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010, 6379, 6443, 7077,
    7443, 7777, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010,
    8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8161, 8443,
    8444, 8445, 8446, 8447, 8448, 8449, 8450, 9000, 9001, 9002, 9003, 9004, 9005,
    9006, 9007, 9008, 9009, 9010, 9200, 9300, 11211, 27017, 27018, 27019, 28017,
    50000, 50070, 50075, 50090, 54321, 60000
]





class ScannerThread(QThread):
    """扫描线程类"""
    progress_updated = pyqtSignal(int)
    result_updated = pyqtSignal(str)
    result_with_port = pyqtSignal(str, int)  # 发送结果和端口号
    scan_finished = pyqtSignal()
    
    def __init__(self, start_ip, end_ip, ports, timeout, max_threads, include_common_ports=False):
        super().__init__()
        self.start_ip = start_ip
        self.end_ip = end_ip
        self.ports = ports
        self.timeout = timeout
        self.max_threads = max_threads
        self.include_common_ports = include_common_ports
        self.hostname_dict = {}  # IP到主机名的映射
        self.is_running = False
        
    def run(self):
        self.is_running = True
        try:
            # 解析IP范围
            start_ip_int = int(ipaddress.IPv4Address(self.start_ip))
            end_ip_int = int(ipaddress.IPv4Address(self.end_ip))
            
            # 解析端口
            port_list = self._parse_ports(self.ports, self.include_common_ports)
            
            # 开始混合扫描：主机名分析 + 端口扫描
            self.result_updated.emit("开始扫描：同时进行主机名分析和端口检测...")
            
            total_ips = end_ip_int - start_ip_int + 1
            total_scans = total_ips * len(port_list)
            current_scan = 0
            
            # 显示扫描信息
            self.result_updated.emit(f"扫描范围：{self.start_ip} - {self.end_ip} ({total_ips} 个IP)")
            self.result_updated.emit(f"端口数量：{len(port_list)} 个端口")
            self.result_updated.emit(f"线程数量：{self.max_threads} 个并发线程")
            self.result_updated.emit("开始端口扫描...")
            
            # 创建线程池
            threads = []
            results = []
            
            for ip_int in range(start_ip_int, end_ip_int + 1):
                if not self.is_running:
                    break
                    
                ip = str(ipaddress.IPv4Address(ip_int))
                
                # 先分析主机名
                hostname = self._get_hostname(ip)
                self.hostname_dict[ip] = hostname
                
                # 然后立即开始端口扫描
                for port in port_list:
                    if not self.is_running:
                        break
                        
                    # 限制并发线程数
                    while len([t for t in threads if t.is_alive()]) >= self.max_threads:
                        time.sleep(0.01)
                        if not self.is_running:
                            break
                    
                    if not self.is_running:
                        break
                    
                    # 创建扫描线程
                    scan_thread = threading.Thread(
                        target=self._scan_port,
                        args=(ip, port, results, self.result_updated)
                    )
                    scan_thread.daemon = True
                    scan_thread.start()
                    threads.append(scan_thread)
                    
                    current_scan += 1
                    progress = int((current_scan / total_scans) * 100)
                    self.progress_updated.emit(progress)
            
            # 等待所有线程完成
            for thread in threads:
                if self.is_running:
                    thread.join()
            
            # 检查是否有结果
            if not results:
                self.result_updated.emit("扫描完成！未发现开放端口。")
            else:
                self.result_updated.emit(f"扫描完成！共发现 {len(results)} 个开放端口。")
                
        except Exception as e:
            self.result_updated.emit(f"扫描出错: {str(e)}\n")
        
        self.scan_finished.emit()
    
    def stop(self):
        self.is_running = False
    

    
    def _get_hostname(self, ip):
        """获取主机名"""
        try:
            # 设置DNS查询超时 - 缩短到0.3秒
            socket.setdefaulttimeout(0.3)
            
            # 尝试通过反向DNS查询获取主机名
            hostname = socket.gethostbyaddr(ip)[0]
            
            # 如果返回的是IP地址本身，说明没有主机名记录
            if hostname == ip:
                return "Unknown"
            
            return hostname
        except (socket.herror, socket.gaierror, OSError, socket.timeout):
            return "Unknown"
        finally:
            # 恢复默认超时设置
            socket.setdefaulttimeout(None)
    
    def _get_device_type_fast(self, ip):
        """快速设备类型检测 - 只检测最常用的端口"""
        try:
            # 只检测最常用的几个端口，超时时间缩短
            common_ports = {
                80: "Web-Device",       # HTTP
                443: "Web-Device",      # HTTPS
                22: "Linux-Device",     # SSH
                3389: "RDP-Device",     # RDP
            }
            
            for port, device_type in common_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(0.3)  # 缩短到0.3秒超时
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        return device_type
                except:
                    continue
            
            return "Network-Device"  # 默认网络设备
            
        except Exception:
            return "Network-Device"
    
    def _get_device_type(self, ip):
        """通过端口检测获取设备类型"""
        try:
            # 检测常见端口来判断设备类型
            common_ports = {
                137: "Windows-Device",  # NetBIOS
                445: "Windows-Device",  # SMB
                22: "Linux-Device",     # SSH
                23: "Telnet-Device",    # Telnet
                80: "Web-Device",       # HTTP
                443: "Web-Device",      # HTTPS
                3389: "RDP-Device",     # RDP
                5900: "VNC-Device",     # VNC
                3306: "MySQL-Device",   # MySQL
                5432: "PostgreSQL-Device", # PostgreSQL
            }
            
            for port, device_type in common_ports.items():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3.0)  # 设置3秒超时
                    result = sock.connect_ex((ip, port))
                    sock.close()
                    
                    if result == 0:
                        return device_type
                except:
                    continue
            
            return "Network-Device"  # 默认网络设备
            
        except Exception:
            return "Network-Device"
    
    def _parse_ports(self, ports_str, include_common_ports=False):
        """解析端口字符串"""
        port_list = []
        parts = ports_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 端口范围
                try:
                    start_port, end_port = part.split('-')
                    start_port = int(start_port.strip())
                    end_port = int(end_port.strip())
                    
                    if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                        port_list.extend(range(start_port, end_port + 1))
                except ValueError:
                    continue
            else:
                # 单个端口
                try:
                    port = int(part)
                    if 1 <= port <= 65535:
                        port_list.append(port)
                except ValueError:
                    continue
        
        # 如果启用常见端口检测，添加常见端口
        if include_common_ports:
            port_list.extend(COMMON_PORTS)
        
        return list(set(port_list))  # 去重
    
    def _scan_port(self, ip, port, results, result_signal):
        """扫描单个端口"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout / 1000.0)  # 转换为秒
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                # 检测服务类型
                service_info = self._detect_service(ip, port, sock)
                results.append((ip, port, service_info))
                
                # 实时显示结果
                hostname = self.hostname_dict.get(ip, "Unknown")
                result_text = f"{ip}:{port} -{hostname}- {service_info}"
                result_signal.emit(result_text)
                # 发送带端口号的结果用于颜色标记
                self.result_with_port.emit(result_text, port)
            
            sock.close()
                
        except Exception:
            pass
    
    def _detect_service(self, ip, port, sock):
        """检测服务类型"""
        try:
            # 常见端口服务映射
            service_map = {
                # 基础网络服务
                20: "FTP-DATA",
                21: "FTP",
                22: "SSH",
                23: "TELNET",
                25: "SMTP",
                53: "DNS",
                67: "DHCP-Server",
                68: "DHCP-Client",
                69: "TFTP",
                80: "HTTP",
                110: "POP3",
                123: "NTP",
                135: "RPC",
                137: "NetBIOS-NS",
                138: "NetBIOS-DGM",
                139: "NetBIOS-SSN",
                143: "IMAP",
                161: "SNMP",
                162: "SNMP-TRAP",
                389: "LDAP",
                443: "HTTPS",
                445: "SMB",
                465: "SMTPS",
                514: "Syslog",
                515: "LPR",
                520: "RIP",
                548: "AFP",
                554: "RTSP",
                587: "SMTP-Submission",
                631: "IPP",
                636: "LDAPS",
                993: "IMAPS",
                995: "POP3S",
                1080: "SOCKS",
                1433: "MSSQL",
                1434: "MSSQL-Browser",
                1521: "Oracle",
                1723: "PPTP",
                2049: "NFS",
                2181: "ZooKeeper",
                3306: "MySQL",
                3389: "RDP",
                5432: "PostgreSQL",
                5900: "VNC",
                5901: "VNC-1",
                5902: "VNC-2",
                5903: "VNC-3",
                5984: "CouchDB",
                6379: "Redis",
                7077: "Spark",
                8080: "HTTP-Proxy",
                8081: "HTTP-Alt",
                8082: "HTTP-Alt",
                8083: "HTTP-Alt",
                8084: "HTTP-Alt",
                8085: "HTTP-Alt",
                8086: "HTTP-Alt",
                8087: "HTTP-Alt",
                8088: "HTTP-Alt",
                8089: "HTTP-Alt",
                8090: "HTTP-Alt",
                8443: "HTTPS-Alt",
                8444: "HTTPS-Alt",
                8445: "HTTPS-Alt",
                8446: "HTTPS-Alt",
                8447: "HTTPS-Alt",
                8448: "HTTPS-Alt",
                8449: "HTTPS-Alt",
                8450: "HTTPS-Alt",
                9000: "HTTP-Alt",
                9001: "HTTP-Alt",
                9002: "HTTP-Alt",
                9003: "HTTP-Alt",
                9004: "HTTP-Alt",
                9005: "HTTP-Alt",
                9006: "HTTP-Alt",
                9007: "HTTP-Alt",
                9008: "HTTP-Alt",
                9009: "HTTP-Alt",
                9010: "HTTP-Alt",
                9200: "Elasticsearch",
                9300: "Elasticsearch-Cluster",
                11211: "Memcached",
                27017: "MongoDB",
                27018: "MongoDB-Shard",
                27019: "MongoDB-Config",
                28017: "MongoDB-Web",
                5000: "Synology-HTTP",
                5001: "Synology-HTTPS",
                5002: "Synology-HTTP",
                5003: "Synology-HTTPS",
                5004: "Synology-HTTP",
                5005: "Synology-HTTPS",
                5006: "Synology-HTTP",
                5007: "Synology-HTTPS",
                5008: "Synology-HTTP",
                5009: "Synology-HTTPS",
                5010: "Synology-HTTP",
                5060: "SIP",
                5061: "SIPS",
                5432: "PostgreSQL",
                5671: "AMQP-SSL",
                5672: "AMQP",
                5900: "VNC",
                5901: "VNC-1",
                5902: "VNC-2",
                5903: "VNC-3",
                5904: "VNC-4",
                5905: "VNC-5",
                5906: "VNC-6",
                5907: "VNC-7",
                5908: "VNC-8",
                5909: "VNC-9",
                5910: "VNC-10",
                5984: "CouchDB",
                6000: "X11",
                6001: "X11-1",
                6002: "X11-2",
                6003: "X11-3",
                6004: "X11-4",
                6005: "X11-5",
                6006: "X11-6",
                6007: "X11-7",
                6008: "X11-8",
                6009: "X11-9",
                6010: "X11-10",
                6379: "Redis",
                6443: "Kubernetes-API",
                7077: "Spark",
                7443: "HTTPS-Alt",
                7777: "Game-Server",
                8000: "HTTP-Alt",
                8001: "HTTP-Alt",
                8002: "HTTP-Alt",
                8003: "HTTP-Alt",
                8004: "HTTP-Alt",
                8005: "HTTP-Alt",
                8006: "HTTP-Alt",
                8007: "HTTP-Alt",
                8008: "HTTP-Alt",
                8009: "HTTP-Alt",
                8010: "HTTP-Alt",
                8080: "HTTP-Proxy",
                8081: "HTTP-Alt",
                8082: "HTTP-Alt",
                8083: "HTTP-Alt",
                8084: "HTTP-Alt",
                8085: "HTTP-Alt",
                8086: "HTTP-Alt",
                8087: "HTTP-Alt",
                8088: "HTTP-Alt",
                8089: "HTTP-Alt",
                8090: "HTTP-Alt",
                8161: "ActiveMQ-Admin",
                8443: "HTTPS-Alt",
                8444: "HTTPS-Alt",
                8445: "HTTPS-Alt",
                8446: "HTTPS-Alt",
                8447: "HTTPS-Alt",
                8448: "HTTPS-Alt",
                8449: "HTTPS-Alt",
                8450: "HTTPS-Alt",
                9000: "HTTP-Alt",
                9001: "HTTP-Alt",
                9002: "HTTP-Alt",
                9003: "HTTP-Alt",
                9004: "HTTP-Alt",
                9005: "HTTP-Alt",
                9006: "HTTP-Alt",
                9007: "HTTP-Alt",
                9008: "HTTP-Alt",
                9009: "HTTP-Alt",
                9010: "HTTP-Alt",
                9200: "Elasticsearch",
                9300: "Elasticsearch-Cluster",
                11211: "Memcached",
                27017: "MongoDB",
                27018: "MongoDB-Shard",
                27019: "MongoDB-Config",
                28017: "MongoDB-Web",
                50000: "DB2",
                50070: "Hadoop-NameNode",
                50075: "Hadoop-DataNode",
                50090: "Hadoop-SecondaryNameNode",
                54321: "VNC-Alt",
                60000: "VNC-Alt"
            }
            
            # 获取基础服务名称
            service_name = service_map.get(port, "UNKNOWN")
            
            # 特殊服务检测
            if port == 80 or port in [8080, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8088, 8089, 8090, 8000, 8001, 8002, 8003, 8004, 8005, 8006, 8007, 8008, 8009, 8010, 9000, 9001, 9002, 9003, 9004, 9005, 9006, 9007, 9008, 9009, 9010]:
                return self._detect_http_service(ip, port, sock, service_name)
            elif port == 443 or port in [8443, 8444, 8445, 8446, 8447, 8448, 8449, 8450, 7443]:
                return self._detect_https_service(ip, port, sock, service_name)
            elif port == 3389:
                return self._detect_rdp_service(ip, port, sock, service_name)
            elif port == 3306:
                return self._detect_mysql_service(ip, port, sock, service_name)
            elif port == 22:
                return self._detect_ssh_service(ip, port, sock, service_name)
            elif port == 21:
                return self._detect_ftp_service(ip, port, sock, service_name)
            elif port in [5000, 5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008, 5009, 5010]:
                return self._detect_synology_service(ip, port, sock, service_name)
            elif port == 27017 or port in [27018, 27019, 28017]:
                return self._detect_mongodb_service(ip, port, sock, service_name)
            elif port == 9200 or port == 9300:
                return self._detect_elasticsearch_service(ip, port, sock, service_name)
            elif port == 11211:
                return self._detect_memcached_service(ip, port, sock, service_name)
            elif port == 6379:
                return self._detect_redis_service(ip, port, sock, service_name)
            elif port == 5432:
                return self._detect_postgresql_service(ip, port, sock, service_name)
            elif port == 1433 or port == 1434:
                return self._detect_mssql_service(ip, port, sock, service_name)
            elif port == 1521:
                return self._detect_oracle_service(ip, port, sock, service_name)
            elif port in [5900, 5901, 5902, 5903, 5904, 5905, 5906, 5907, 5908, 5909, 5910]:
                return self._detect_vnc_service(ip, port, sock, service_name)
            elif port in [6000, 6001, 6002, 6003, 6004, 6005, 6006, 6007, 6008, 6009, 6010]:
                return self._detect_x11_service(ip, port, sock, service_name)
            elif port == 161:
                return self._detect_snmp_service(ip, port, sock, service_name)
            elif port == 389 or port == 636:
                return self._detect_ldap_service(ip, port, sock, service_name)
            elif port == 25 or port == 587 or port == 465:
                return self._detect_smtp_service(ip, port, sock, service_name)
            elif port in [110, 995]:
                return self._detect_pop3_service(ip, port, sock, service_name)
            elif port in [143, 993]:
                return self._detect_imap_service(ip, port, sock, service_name)
            elif port == 53:
                return self._detect_dns_service(ip, port, sock, service_name)
            elif port == 123:
                return self._detect_ntp_service(ip, port, sock, service_name)
            elif port == 69:
                return self._detect_tftp_service(ip, port, sock, service_name)
            elif port == 514:
                return self._detect_syslog_service(ip, port, sock, service_name)
            elif port == 5060 or port == 5061:
                return self._detect_sip_service(ip, port, sock, service_name)
            elif port == 5672 or port == 5671:
                return self._detect_amqp_service(ip, port, sock, service_name)
            elif port == 8161:
                return self._detect_activemq_service(ip, port, sock, service_name)
            elif port == 6443:
                return self._detect_kubernetes_service(ip, port, sock, service_name)
            elif port == 7077:
                return self._detect_spark_service(ip, port, sock, service_name)
            elif port == 2181:
                return self._detect_zookeeper_service(ip, port, sock, service_name)
            elif port == 5984:
                return self._detect_couchdb_service(ip, port, sock, service_name)
            elif port == 50070 or port == 50075 or port == 50090:
                return self._detect_hadoop_service(ip, port, sock, service_name)
            elif port == 50000:
                return self._detect_db2_service(ip, port, sock, service_name)
            else:
                return f"{service_name} ON"
                
        except Exception:
            return "UNKNOWN ON"
    
    def _detect_http_service(self, ip, port, sock, service_name):
        """检测HTTP服务"""
        try:
            # 发送HTTP GET请求
            request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
            sock.send(request.encode())
            
            # 接收响应
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "HTTP/1." in response or "HTTP/2." in response:
                # 尝试提取服务器信息
                if "Server:" in response:
                    server_info = ""
                    for line in response.split('\n'):
                        if line.startswith('Server:'):
                            server_info = line.split(':', 1)[1].strip()
                            break
                    if server_info:
                        return f"{service_name} ON ({server_info})"
                    else:
                        return f"{service_name} ON"
                else:
                    return f"{service_name} ON"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_https_service(self, ip, port, sock, service_name):
        """检测HTTPS服务"""
        try:
            # HTTPS服务检测（简化版）
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_rdp_service(self, ip, port, sock, service_name):
        """检测RDP服务"""
        try:
            # 发送RDP连接请求
            rdp_request = b'\x03\x00\x00\x13\x0e\xe0\x00\x00\x00\x00\x00\x01\x00\x08\x00\x03\x00\x00\x00'
            sock.send(rdp_request)
            
            # 接收响应
            response = sock.recv(1024)
            
            if response and len(response) > 0:
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_mysql_service(self, ip, port, sock, service_name):
        """检测MySQL服务"""
        try:
            # 发送MySQL握手包
            mysql_request = b'\x0a'
            sock.send(mysql_request)
            
            # 接收响应
            response = sock.recv(1024)
            
            if response and len(response) > 0:
                # 检查MySQL协议标识
                if response[0] == 10:  # MySQL协议版本
                    return f"{service_name} ON"
                else:
                    return f"{service_name} ON"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_ssh_service(self, ip, port, sock, service_name):
        """检测SSH服务"""
        try:
            # 接收SSH banner
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "SSH" in response:
                # 提取SSH版本信息
                lines = response.split('\n')
                for line in lines:
                    if "SSH" in line:
                        return f"{service_name} ON ({line.strip()})"
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_ftp_service(self, ip, port, sock, service_name):
        """检测FTP服务"""
        try:
            # 接收FTP banner
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if response.startswith('220'):
                # 提取FTP服务器信息
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('220'):
                        server_info = line[4:].strip()
                        return f"{service_name} ON ({server_info})"
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_synology_service(self, ip, port, sock, service_name):
        """检测群晖服务"""
        try:
            if port == 5000:
                # 检测群晖HTTP服务
                request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
                sock.send(request.encode())
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                
                if "Synology" in response or "DSM" in response:
                    return f"{service_name} ON (Synology DSM)"
                else:
                    return f"{service_name} ON"
            elif port == 5001:
                # 检测群晖HTTPS服务
                return f"{service_name} ON (Synology DSM)"
            else:
                return f"{service_name} ON"
                
        except Exception:
            return f"{service_name} ON"
    
    def _detect_mongodb_service(self, ip, port, sock, service_name):
        """检测MongoDB服务"""
        try:
            # MongoDB使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_elasticsearch_service(self, ip, port, sock, service_name):
        """检测Elasticsearch服务"""
        try:
            if port == 9200:
                # 发送HTTP请求到Elasticsearch
                request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
                sock.send(request.encode())
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                
                if "elasticsearch" in response.lower() or "cluster_name" in response.lower():
                    return f"{service_name} ON (Elasticsearch)"
                else:
                    return f"{service_name} ON"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_memcached_service(self, ip, port, sock, service_name):
        """检测Memcached服务"""
        try:
            # Memcached使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_redis_service(self, ip, port, sock, service_name):
        """检测Redis服务"""
        try:
            # 发送Redis PING命令
            redis_ping = b'*1\r\n$4\r\nPING\r\n'
            sock.send(redis_ping)
            response = sock.recv(1024)
            
            if b'PONG' in response:
                return f"{service_name} ON (Redis)"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_postgresql_service(self, ip, port, sock, service_name):
        """检测PostgreSQL服务"""
        try:
            # PostgreSQL使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_mssql_service(self, ip, port, sock, service_name):
        """检测MSSQL服务"""
        try:
            # MSSQL使用TDS协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_oracle_service(self, ip, port, sock, service_name):
        """检测Oracle服务"""
        try:
            # Oracle使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_vnc_service(self, ip, port, sock, service_name):
        """检测VNC服务"""
        try:
            # VNC使用RFB协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_x11_service(self, ip, port, sock, service_name):
        """检测X11服务"""
        try:
            # X11使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_snmp_service(self, ip, port, sock, service_name):
        """检测SNMP服务"""
        try:
            # SNMP使用UDP协议，这里简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_ldap_service(self, ip, port, sock, service_name):
        """检测LDAP服务"""
        try:
            # LDAP使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_smtp_service(self, ip, port, sock, service_name):
        """检测SMTP服务"""
        try:
            # 接收SMTP banner
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if response.startswith('220'):
                # 提取SMTP服务器信息
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('220'):
                        server_info = line[4:].strip()
                        return f"{service_name} ON ({server_info})"
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_pop3_service(self, ip, port, sock, service_name):
        """检测POP3服务"""
        try:
            # 接收POP3 banner
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if response.startswith('+OK'):
                # 提取POP3服务器信息
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('+OK'):
                        server_info = line[4:].strip()
                        return f"{service_name} ON ({server_info})"
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_imap_service(self, ip, port, sock, service_name):
        """检测IMAP服务"""
        try:
            # 接收IMAP banner
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if response.startswith('* OK'):
                # 提取IMAP服务器信息
                lines = response.split('\n')
                for line in lines:
                    if line.startswith('* OK'):
                        server_info = line[5:].strip()
                        return f"{service_name} ON ({server_info})"
                return f"{service_name} ON"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_dns_service(self, ip, port, sock, service_name):
        """检测DNS服务"""
        try:
            # DNS使用UDP协议，这里简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_ntp_service(self, ip, port, sock, service_name):
        """检测NTP服务"""
        try:
            # NTP使用UDP协议，这里简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_tftp_service(self, ip, port, sock, service_name):
        """检测TFTP服务"""
        try:
            # TFTP使用UDP协议，这里简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_syslog_service(self, ip, port, sock, service_name):
        """检测Syslog服务"""
        try:
            # Syslog使用UDP协议，这里简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_sip_service(self, ip, port, sock, service_name):
        """检测SIP服务"""
        try:
            # SIP使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_amqp_service(self, ip, port, sock, service_name):
        """检测AMQP服务"""
        try:
            # AMQP使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_activemq_service(self, ip, port, sock, service_name):
        """检测ActiveMQ服务"""
        try:
            # 发送HTTP请求到ActiveMQ管理界面
            request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
            sock.send(request.encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "activemq" in response.lower() or "apache" in response.lower():
                return f"{service_name} ON (ActiveMQ)"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_kubernetes_service(self, ip, port, sock, service_name):
        """检测Kubernetes服务"""
        try:
            # 发送HTTP请求到Kubernetes API
            request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
            sock.send(request.encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "kubernetes" in response.lower() or "api" in response.lower():
                return f"{service_name} ON (Kubernetes)"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_spark_service(self, ip, port, sock, service_name):
        """检测Spark服务"""
        try:
            # Spark使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_zookeeper_service(self, ip, port, sock, service_name):
        """检测ZooKeeper服务"""
        try:
            # ZooKeeper使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_couchdb_service(self, ip, port, sock, service_name):
        """检测CouchDB服务"""
        try:
            # 发送HTTP请求到CouchDB
            request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
            sock.send(request.encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "couchdb" in response.lower() or "couch" in response.lower():
                return f"{service_name} ON (CouchDB)"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_hadoop_service(self, ip, port, sock, service_name):
        """检测Hadoop服务"""
        try:
            # 发送HTTP请求到Hadoop管理界面
            request = "GET / HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(ip)
            sock.send(request.encode())
            response = sock.recv(1024).decode('utf-8', errors='ignore')
            
            if "hadoop" in response.lower() or "namenode" in response.lower():
                return f"{service_name} ON (Hadoop)"
            else:
                return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"
    
    def _detect_db2_service(self, ip, port, sock, service_name):
        """检测DB2服务"""
        try:
            # DB2使用自定义协议，简化检测
            return f"{service_name} ON"
        except Exception:
            return f"{service_name} ON"


class IPScannerGUI(QMainWindow):
    """IP扫描器GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.scanner_thread = None
        self.result_line_count = 0  # 用于交替背景色
        self.init_ui()
        
        # 设置窗口标题
        self.setWindowTitle("局域网IP端口扫描器 - By wangzhenjjcn")
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("局域网IP端口扫描器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 信息设置区
        self.create_settings_group(main_layout)
        
        # 扫描结果区
        self.create_results_group(main_layout)
        
        # 颜色图例区
        self.create_color_legend(main_layout)
        
        # 按钮区
        self.create_buttons(main_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
    def create_settings_group(self, parent_layout):
        """创建信息设置区"""
        settings_group = QGroupBox("信息设置")
        settings_layout = QGridLayout()
        
        # 获取本地IP和子网信息
        local_ip, start_ip, end_ip, subnet_mask = get_local_ip_and_subnet()
        
        # 显示本地IP信息
        local_ip_label = QLabel(f"本地IP: {local_ip} (子网: /{subnet_mask})")
        local_ip_label.setStyleSheet("color: #666; font-size: 9px;")
        settings_layout.addWidget(local_ip_label, 0, 0, 1, 4)
        
        # 起始IP
        settings_layout.addWidget(QLabel("起始IP:"), 1, 0)
        self.start_ip_edit = QLineEdit(start_ip)
        self.start_ip_edit.setPlaceholderText("例如: 192.168.0.1")
        settings_layout.addWidget(self.start_ip_edit, 1, 1)
        
        # 结束IP
        settings_layout.addWidget(QLabel("结束IP:"), 1, 2)
        self.end_ip_edit = QLineEdit(end_ip)
        self.end_ip_edit.setPlaceholderText("例如: 192.168.1.255")
        settings_layout.addWidget(self.end_ip_edit, 1, 3)
        
        # 端口号
        settings_layout.addWidget(QLabel("端口号:"), 2, 0)
        self.ports_edit = QLineEdit("80,443,3389,138-139,3306,22,21,23,25,53,110,143,445,993,995,1433,1521,5432,5900,6379,8080,8443,9000,9200,11211,27017,5000-5010,5900-5910,6000-6010,8000-8010,8080-8090,8443-8450,9000-9010")
        self.ports_edit.setPlaceholderText("例如: 80,443,3389,138-139,3306,22,21,23,25,53,110,143,445,993,995,1433,1521,5432,5900,6379,8080,8443,9000,9200,11211,27017,5000-5010,5900-5910,6000-6010,8000-8010,8080-8090,8443-8450,9000-9010")
        settings_layout.addWidget(self.ports_edit, 2, 1, 1, 2)
        
        # 常见端口检测选项
        self.common_ports_checkbox = QCheckBox("检测常见端口")
        self.common_ports_checkbox.setToolTip("勾选后将自动检测所有常见端口，同时保留手动输入的端口")
        settings_layout.addWidget(self.common_ports_checkbox, 2, 3)
        
        # 超时
        settings_layout.addWidget(QLabel("超时(毫秒):"), 3, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(100, 9999)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" ms")
        settings_layout.addWidget(self.timeout_spin, 3, 1)
        
        # 线程数
        settings_layout.addWidget(QLabel("线程数:"), 3, 2)
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 9999)
        self.threads_spin.setValue(500)
        settings_layout.addWidget(self.threads_spin, 3, 3)
        
        settings_group.setLayout(settings_layout)
        parent_layout.addWidget(settings_group)
        
    def create_copyright_group(self, parent_layout):
        """创建版权信息区"""
        # 这个方法现在为空，版权信息按钮将移到按钮区
        pass
    
    def show_copyright_info(self):
        """显示版权信息弹窗"""
        copyright_text = """
IP端口扫描器

Copyright (c) 2024 wangzhenjjcn@gmail.com
Author: wangzhenjjcn
GitHub: https://github.com/wangzhenjjcn/WinTools

功能特点：
• 图形化用户界面，操作简单
• 支持IP范围扫描
• 支持单个端口和端口范围扫描
• 可配置超时时间和线程数
• 实时显示扫描进度和结果
• 多线程并发扫描，提高效率
• 智能服务检测：自动检测常见端口的服务类型
• 详细服务信息：显示服务名称和版本信息
• 主机名显示：自动检测并显示目标设备的主机名
• 常见端口检测：一键检测所有常见端口

使用说明：
1. 设置起始IP和结束IP
2. 输入要扫描的端口或勾选"检测常见端口"
3. 设置超时时间和线程数
4. 点击"开始扫描"按钮
5. 在结果区查看扫描结果

注意事项：
• 请确保您有权限扫描目标网络
• 大量并发连接可能会被防火墙拦截
• 建议在本地网络环境中使用
• 扫描时间取决于网络环境和目标数量
• 服务检测会增加扫描时间，但提供更详细的信息
        """
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("版权信息")
        msg_box.setText(copyright_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def create_results_group(self, parent_layout):
        """创建扫描结果区"""
        results_group = QGroupBox("扫描结果")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        
        # 设置文档边距
        document = self.results_text.document()
        document.setDocumentMargin(2)
        
        # 设置样式表减少行距
        self.results_text.setStyleSheet("""
            QTextEdit {
                padding: 4px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
                line-height: 1.2;
            }
        """)
        
        # 启用HTML支持
        self.results_text.setAcceptRichText(True)
        
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        parent_layout.addWidget(results_group)
        
    def create_buttons(self, parent_layout):
        """创建按钮区"""
        button_layout = QHBoxLayout()
        
        self.scan_button = QPushButton("开始扫描")
        self.scan_button.clicked.connect(self.start_scan)
        button_layout.addWidget(self.scan_button)
        
        self.stop_button = QPushButton("停止扫描")
        self.stop_button.clicked.connect(self.stop_scan)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        
        # 版权信息按钮
        self.copyright_button = QPushButton("版权信息")
        self.copyright_button.clicked.connect(self.show_copyright_info)
        button_layout.addWidget(self.copyright_button)
        
        self.exit_button = QPushButton("退出程序")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)
        
        parent_layout.addLayout(button_layout)
    
    def create_color_legend(self, parent_layout):
        """创建颜色图例"""
        legend_group = QGroupBox("端口类型颜色图例")
        legend_layout = QHBoxLayout()
        
        # 定义图例项
        legend_items = [
            ("Web服务", "web"),
            ("远程访问", "remote"),
            ("数据库", "database"),
            ("邮件服务", "mail"),
            ("文件传输", "file"),
            ("网络服务", "network"),
            ("游戏服务", "game"),
            ("消息队列", "mq"),
            ("监控服务", "monitor"),
            ("其他服务", "other")
        ]
        
        for label, category in legend_items:
            color = self._get_port_color_by_category(category)
            legend_item = QLabel(f"● {label}")
            legend_item.setStyleSheet(f"color: {color}; font-weight: bold; margin: 2px;")
            legend_layout.addWidget(legend_item)
        
        legend_layout.addStretch()
        legend_group.setLayout(legend_layout)
        parent_layout.addWidget(legend_group)
    
    def _get_port_color_by_category(self, category):
        """根据类别获取端口颜色"""
        is_dark_theme = self._is_dark_theme()
        
        color_schemes = {
            'light': {
                'web': '#2E8B57',      # 海绿色
                'remote': '#8A2BE2',    # 蓝紫色
                'database': '#DAA520',  # 金麦色
                'mail': '#DC143C',      # 深红色
                'file': '#4682B4',      # 钢蓝色
                'network': '#32CD32',   # 酸橙绿
                'game': '#FF4500',      # 橙红色
                'mq': '#9370DB',        # 中等紫色
                'monitor': '#20B2AA',   # 浅海绿
                'other': '#696969'      # 暗灰色
            },
            'dark': {
                'web': '#90EE90',       # 浅绿色
                'remote': '#DDA0DD',    # 浅紫色
                'database': '#F0E68C',  # 浅黄色
                'mail': '#FFB6C1',      # 浅粉色
                'file': '#87CEEB',      # 天蓝色
                'network': '#98FB98',   # 浅绿色
                'game': '#FFA07A',      # 浅鲑鱼色
                'mq': '#E6E6FA',        # 淡紫色
                'monitor': '#AFEEEE',   # 浅青色
                'other': '#D3D3D3'      # 浅灰色
            }
        }
        
        scheme = color_schemes['dark'] if is_dark_theme else color_schemes['light']
        return scheme.get(category, scheme['other'])
        
    def validate_inputs(self):
        """验证输入数据"""
        errors = []
        
        # 验证IP地址
        try:
            start_ip = self.start_ip_edit.text().strip()
            end_ip = self.end_ip_edit.text().strip()
            
            ipaddress.IPv4Address(start_ip)
            ipaddress.IPv4Address(end_ip)
            
            # 检查IP范围
            start_ip_int = int(ipaddress.IPv4Address(start_ip))
            end_ip_int = int(ipaddress.IPv4Address(end_ip))
            
            if start_ip_int > end_ip_int:
                errors.append("起始IP不能大于结束IP")
                
        except ipaddress.AddressValueError:
            errors.append("IP地址格式不正确")
        
        # 验证端口
        ports_str = self.ports_edit.text().strip()
        if not ports_str and not self.common_ports_checkbox.isChecked():
            errors.append("端口号不能为空或请勾选检测常见端口")
        else:
            try:
                port_list = self._parse_ports(ports_str, self.common_ports_checkbox.isChecked())
                if not port_list:
                    errors.append("端口号格式不正确")
            except:
                errors.append("端口号格式不正确")
        
        # 验证超时
        timeout = self.timeout_spin.value()
        if timeout < 100 or timeout > 9999:
            errors.append("超时时间必须在100-9999毫秒之间")
        
        # 验证线程数
        threads = self.threads_spin.value()
        if threads < 1 or threads > 9999:
            errors.append("线程数必须在1-9999之间")
        
        return errors
    
    def _parse_ports(self, ports_str, include_common_ports=False):
        """解析端口字符串（用于验证）"""
        port_list = []
        parts = ports_str.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 端口范围
                start_port, end_port = part.split('-')
                start_port = int(start_port.strip())
                end_port = int(end_port.strip())
                
                if 1 <= start_port <= 65535 and 1 <= end_port <= 65535 and start_port <= end_port:
                    port_list.extend(range(start_port, end_port + 1))
            else:
                # 单个端口
                port = int(part)
                if 1 <= port <= 65535:
                    port_list.append(port)
        
        # 如果启用常见端口检测，添加常见端口
        if include_common_ports:
            port_list.extend(COMMON_PORTS)
        
        return list(set(port_list))
    
    def start_scan(self):
        """开始扫描"""
        # 验证输入
        errors = self.validate_inputs()
        if errors:
            QMessageBox.warning(self, "输入错误", "\n".join(errors))
            return
        
        # 清空结果
        self.results_text.clear()
        self.result_line_count = 0  # 重置行计数
        
        # 创建扫描线程
        self.scanner_thread = ScannerThread(
            self.start_ip_edit.text().strip(),
            self.end_ip_edit.text().strip(),
            self.ports_edit.text().strip(),
            self.timeout_spin.value(),
            self.threads_spin.value(),
            self.common_ports_checkbox.isChecked()
        )
        
        # 连接信号
        self.scanner_thread.progress_updated.connect(self.update_progress)
        self.scanner_thread.result_updated.connect(self.update_results)
        self.scanner_thread.result_with_port.connect(self.update_results_with_color)
        self.scanner_thread.scan_finished.connect(self.scan_finished)
        
        # 更新UI状态
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 开始扫描
        self.scanner_thread.start()
    
    def stop_scan(self):
        """停止扫描"""
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
            # 扫描已停止，不添加提示
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def update_results(self, text):
        """更新扫描结果"""
        # 添加换行符确保结果间没有空行
        self.results_text.append(text)
        # 滚动到底部
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)
    
    def update_results_with_color(self, text, port):
        """更新带颜色标记的扫描结果"""
        # 确定端口类型和颜色
        port_color = self._get_port_color(port)
        
        # 获取系统主题适配的背景色
        bg_colors = self._get_background_colors()
        bg_color = bg_colors[0] if self.result_line_count % 2 == 0 else bg_colors[1]
        
        # 创建带颜色的HTML文本
        html_text = f'<div style="background-color: {bg_color}; padding: 2px; margin: 1px 0; border-radius: 2px;">'
        html_text += f'<span style="color: {port_color}; font-weight: 500;">{text}</span></div>'
        
        # 添加到结果文本
        self.results_text.append(html_text)
        
        # 滚动到底部
        cursor = self.results_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.results_text.setTextCursor(cursor)
        
        # 增加行计数
        self.result_line_count += 1
    
    def _get_background_colors(self):
        """获取适配系统主题的背景色"""
        is_dark_theme = self._is_dark_theme()
        
        if is_dark_theme:
            # 暗色主题背景色
            return ["#2d2d2d", "#3a3a3a"]  # 深灰交替
        else:
            # 明色主题背景色
            return ["#f8f9fa", "#ffffff"]   # 浅灰交替
    
    def _get_port_color(self, port):
        """根据端口号确定颜色"""
        # 获取系统主题
        is_dark_theme = self._is_dark_theme()
        
        # 端口分类定义
        port_categories = {
            # Web服务端口
            'web': [80, 443, 8080, 8443, 8000, 8001, 8002, 8003, 8004, 8005, 
                   8006, 8007, 8008, 8009, 8010, 8081, 8082, 8083, 8084, 8085,
                   8086, 8087, 8088, 8089, 8090, 9000, 9001, 9002, 9003, 9004,
                   9005, 9006, 9007, 9008, 9009, 9010, 8444, 8445, 8446, 8447,
                   8448, 8449, 8450, 7443, 8161],
            
            # 远程访问端口
            'remote': [22, 23, 3389, 5900, 5901, 5902, 5903, 5904, 5905, 5906,
                      5907, 5908, 5909, 5910, 6000, 6001, 6002, 6003, 6004, 6005,
                      6006, 6007, 6008, 6009, 6010, 54321, 60000],
            
            # 数据库端口
            'database': [3306, 5432, 1433, 1434, 1521, 27017, 27018, 27019, 28017,
                        6379, 11211, 5984, 50000, 50070, 50075, 50090],
            
            # 邮件服务端口
            'mail': [25, 110, 143, 465, 587, 993, 995],
            
            # 文件传输端口
            'file': [20, 21, 69, 445, 548, 2049],
            
            # 网络服务端口
            'network': [53, 67, 68, 123, 135, 137, 138, 139, 161, 162, 389, 636, 514, 515, 520],
            
            # 游戏服务端口
            'game': [7777],
            
            # 消息队列端口
            'mq': [5671, 5672],
            
            # 监控端口
            'monitor': [2181, 7077, 9200, 9300],
            
            # 其他服务端口
            'other': [1080, 1433, 1521, 1723, 2181, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 9000, 9200, 11211, 27017]
        }
        
        # 颜色方案（支持明暗主题）
        color_schemes = {
            'light': {
                'web': '#2E8B57',      # 海绿色
                'remote': '#8A2BE2',    # 蓝紫色
                'database': '#DAA520',  # 金麦色
                'mail': '#DC143C',      # 深红色
                'file': '#4682B4',      # 钢蓝色
                'network': '#32CD32',   # 酸橙绿
                'game': '#FF4500',      # 橙红色
                'mq': '#9370DB',        # 中等紫色
                'monitor': '#20B2AA',   # 浅海绿
                'other': '#696969'      # 暗灰色
            },
            'dark': {
                'web': '#90EE90',       # 浅绿色
                'remote': '#DDA0DD',    # 浅紫色
                'database': '#F0E68C',  # 浅黄色
                'mail': '#FFB6C1',      # 浅粉色
                'file': '#87CEEB',      # 天蓝色
                'network': '#98FB98',   # 浅绿色
                'game': '#FFA07A',      # 浅鲑鱼色
                'mq': '#E6E6FA',        # 淡紫色
                'monitor': '#AFEEEE',   # 浅青色
                'other': '#D3D3D3'      # 浅灰色
            }
        }
        
        # 选择颜色方案
        scheme = color_schemes['dark'] if is_dark_theme else color_schemes['light']
        
        # 确定端口类别
        for category, ports in port_categories.items():
            if port in ports:
                return scheme[category]
        
        # 默认颜色
        return scheme['other']
    
    def _is_dark_theme(self):
        """检测系统是否为暗色主题"""
        try:
            palette = self.palette()
            background_color = palette.color(QPalette.ColorRole.Window)
            # 计算背景色的亮度
            brightness = (background_color.red() * 299 + background_color.green() * 587 + background_color.blue() * 114) / 1000
            return brightness < 128
        except:
            return False
    
    def scan_finished(self):
        """扫描完成"""
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        # 扫描完成，不添加额外提示


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("IP端口扫描器")
    
    window = IPScannerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 