"""
Network scanner service for device discovery using ARP and Nmap.
"""
import asyncio
import ipaddress
import logging
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    from scapy.all import ARP, Ether, srp, conf as scapy_conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    scapy_conf = None

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.device import Device, DeviceHistory, DeviceType
from app.services.websocket_manager import get_websocket_manager
from app.database import get_session


logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Discovered device information."""
    mac_address: str
    ip_address: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None


class NetworkScanner:
    """Network device scanner using ARP and Nmap."""

    def __init__(self):
        self.settings = get_settings()
        self._is_scanning = False
        self._scan_task: Optional[asyncio.Task] = None

    @property
    def is_scanning(self) -> bool:
        return self._is_scanning

    async def get_local_network_cidr(self) -> str:
        """Detect local network CIDR."""
        import socket

        try:
            import netifaces
            gateways = netifaces.gateways()
            default_gateway = gateways.get("default", {}).get(netifaces.AF_INET)
            if default_gateway:
                interface = default_gateway[1]
                addrs = netifaces.ifaddresses(interface)
                inet_info = addrs.get(netifaces.AF_INET, [{}])[0]
                ip = inet_info.get("addr")
                netmask = inet_info.get("netmask")
                if ip and netmask:
                    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
                    return str(network)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to auto-detect network via netifaces: {e}")

        # Fallback: try to get from local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            # Assume /24
            network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
            return str(network)
        except Exception:
            pass

        return "192.168.1.0/24"

    async def arp_scan(self, network_cidr: Optional[str] = None) -> List[DiscoveredDevice]:
        """Perform ARP scan to discover devices."""
        if network_cidr is None:
            network_cidr = await self.get_local_network_cidr()

        logger.info(f"Starting ARP scan on {network_cidr}")

        if SCAPY_AVAILABLE:
            return await self._arp_scan_scapy(network_cidr)
        else:
            return await self._arp_scan_arp_table(network_cidr)

    async def _arp_scan_scapy(self, network_cidr: str) -> List[DiscoveredDevice]:
        """ARP scan using scapy (requires admin/WinPcap)."""
        try:
            arp = ARP(pdst=network_cidr)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp

            scapy_conf.verb = 0
            result = srp(packet, timeout=self.settings.arp_scan_timeout, verbose=False)[0]

            devices = []
            for sent, received in result:
                mac = received.hwsrc.upper()
                ip = received.psrc
                hostname = None
                try:
                    import socket
                    hostname = socket.gethostbyaddr(ip)[0]
                except Exception:
                    pass
                vendor = self._get_vendor_from_mac(mac)
                devices.append(DiscoveredDevice(mac_address=mac, ip_address=ip, hostname=hostname, vendor=vendor))

            logger.info(f"Scapy ARP scan found {len(devices)} devices")
            return devices
        except Exception as e:
            logger.error(f"Scapy ARP scan failed: {e}")
            return []

    async def _arp_scan_arp_table(self, network_cidr: str) -> List[DiscoveredDevice]:
        """Fallback: read the OS ARP table (no admin required)."""
        import socket
        devices = []
        try:
            # Ping sweep to populate ARP table
            network = ipaddress.IPv4Network(network_cidr, strict=False)
            # Only ping small networks to avoid flooding
            hosts = list(network.hosts())
            if len(hosts) > 254:
                hosts = hosts[:254]

            ping_tasks = []
            for host in hosts:
                ping_tasks.append(asyncio.create_subprocess_exec(
                    "ping", "-n", "1", "-w", "200", str(host),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                ))

            procs = await asyncio.gather(*[t for t in ping_tasks], return_exceptions=True)
            # Wait for all pings
            for proc in procs:
                if hasattr(proc, 'wait'):
                    try:
                        await asyncio.wait_for(proc.wait(), timeout=1.0)
                    except asyncio.TimeoutError:
                        try: proc.kill()
                        except: pass

            # Read ARP table
            proc = await asyncio.create_subprocess_exec(
                "arp", "-a",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await proc.communicate()
            arp_output = stdout.decode(errors='replace')

            import re
            # Parse Windows ARP output: "  192.168.1.1          00-11-22-33-44-55     dynamic"
            for line in arp_output.splitlines():
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})', line)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).replace('-', ':').upper()
                    if mac == 'FF:FF:FF:FF:FF:FF': continue

                    hostname = None
                    try:
                        hostname = socket.gethostbyaddr(ip)[0]
                    except Exception:
                        pass

                    vendor = self._get_vendor_from_mac(mac)
                    devices.append(DiscoveredDevice(mac_address=mac, ip_address=ip, hostname=hostname, vendor=vendor))

            logger.info(f"ARP table scan found {len(devices)} devices")
        except Exception as e:
            logger.error(f"ARP table scan failed: {e}")

        return devices

    def _get_vendor_from_mac(self, mac: str) -> Optional[str]:
        """Get vendor from MAC address OUI (simplified)."""
        # This is a simplified version - in production you'd use a full OUI database
        oui_database = {
            "00:1A:2B": "Apple",
            "00:1B:63": "Apple",
            "00:1C:B3": "Apple",
            "00:1D:4F": "Apple",
            "00:1E:52": "Apple",
            "00:1F:5B": "Apple",
            "00:21:E9": "Apple",
            "00:22:41": "Apple",
            "00:23:12": "Apple",
            "00:23:6C": "Apple",
            "00:24:36": "Apple",
            "00:25:00": "Apple",
            "00:25:4B": "Apple",
            "00:26:08": "Apple",
            "00:26:4A": "Apple",
            "00:26:B0": "Apple",
            "00:26:BB": "Apple",
            "00:17:F2": "Dell",
            "00:18:8B": "Dell",
            "00:19:B9": "Dell",
            "00:1A:4D": "Dell",
            "00:1B:24": "Dell",
            "00:1C:23": "Dell",
            "00:1D:09": "Dell",
            "00:1E:4F": "Dell",
            "00:1F:1F": "Dell",
            "00:21:70": "Dell",
            "00:22:19": "Dell",
            "00:23:AE": "Dell",
            "00:24:E8": "Dell",
            "00:25:64": "Dell",
            "00:26:B9": "Dell",
            "00:0C:29": "VMware",
            "00:50:56": "VMware",
            "00:1C:14": "VMware",
            "00:03:FF": "Microsoft",
            "00:15:5D": "Microsoft",
            "00:1D:D8": "Microsoft",
            "00:22:48": "Microsoft",
            "00:24:81": "Microsoft",
            "00:25:AE": "Microsoft",
            "00:1C:42": "Parallels",
            "00:05:69": "VMware",
            "00:16:3E": "Xen",
            "52:54:00": "QEMU/KVM",
        }
        oui = mac[:8].upper()
        return oui_database.get(oui)

    async def nmap_scan(self, target_ip: str) -> Dict[str, Any]:
        """Perform Nmap service/port scan on a target."""
        try:
            # Run nmap with XML output
            cmd = [
                self.settings.nmap_path,
                "-sS",  # SYN scan
                "-sV",  # Version detection
                "-O",   # OS detection
                "--top-ports", "100",
                "-oX", "-",  # XML output to stdout
                target_ip,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.warning(f"Nmap scan failed for {target_ip}: {stderr.decode()}")
                return {}

            # Parse XML
            return self._parse_nmap_xml(stdout.decode())

        except FileNotFoundError:
            logger.warning("Nmap not found, skipping service scan")
            return {}
        except Exception as e:
            logger.error(f"Nmap scan error for {target_ip}: {e}")
            return {}

    def _parse_nmap_xml(self, xml_output: str) -> Dict[str, Any]:
        """Parse Nmap XML output."""
        try:
            root = ET.fromstring(xml_output)
            result = {
                "services": [],
                "os_info": None,
            }

            for host in root.findall("host"):
                # Get OS info
                os_elem = host.find("os")
                if os_elem is not None:
                    os_match = os_elem.find("osmatch")
                    if os_match is not None:
                        result["os_info"] = os_match.get("name")

                # Get ports/services
                ports_elem = host.find("ports")
                if ports_elem is not None:
                    for port_elem in ports_elem.findall("port"):
                        port_id = int(port_elem.get("portid", 0))
                        protocol = port_elem.get("protocol", "tcp")
                        state_elem = port_elem.find("state")
                        state = state_elem.get("state") if state_elem is not None else "unknown"

                        service_elem = port_elem.find("service")
                        service_name = service_elem.get("name") if service_elem is not None else "unknown"
                        service_version = service_elem.get("version") if service_elem is not None else ""
                        service_product = service_elem.get("product") if service_elem is not None else ""

                        service_info = f"{service_name}"
                        if service_product:
                            service_info += f" {service_product}"
                        if service_version:
                            service_info += f" {service_version}"

                        result["services"].append({
                            "port": port_id,
                            "protocol": protocol,
                            "service": service_info.strip(),
                            "state": state,
                        })

            return result

        except ET.ParseError as e:
            logger.error(f"Failed to parse Nmap XML: {e}")
            return {}

    async def update_device_from_discovery(
        self,
        db: AsyncSession,
        discovered: DiscoveredDevice,
    ) -> Device:
        """Update or create device from discovery."""
        # Check if device exists
        result = await db.execute(
            select(Device).where(Device.mac_address == discovered.mac_address)
        )
        device = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if device:
            # Update existing device
            was_offline = not device.is_online
            ip_changed = device.ip_address != discovered.ip_address

            device.ip_address = discovered.ip_address
            device.hostname = discovered.hostname or device.hostname
            device.vendor = discovered.vendor or device.vendor
            device.is_online = True
            device.last_seen = now

            if was_offline:
                # Device came online
                history = DeviceHistory(
                    device_id=device.id,
                    ip_address=discovered.ip_address,
                    event_type="online",
                    details=f"Device came online at {discovered.ip_address}",
                )
                db.add(history)

                # Notify via WebSocket
                ws_manager = get_websocket_manager()
                await ws_manager.broadcast_device_status(device.id, True)

            if ip_changed:
                history = DeviceHistory(
                    device_id=device.id,
                    ip_address=discovered.ip_address,
                    event_type="ip_change",
                    details=f"IP changed to {discovered.ip_address}",
                )
                db.add(history)

        else:
            # Create new device
            device = Device(
                mac_address=discovered.mac_address,
                ip_address=discovered.ip_address,
                hostname=discovered.hostname,
                vendor=discovered.vendor,
                device_type=self._guess_device_type(discovered),
                is_online=True,
                is_known=False,
                is_authorized=False,
            )
            db.add(device)
            await db.flush()

            history = DeviceHistory(
                device_id=device.id,
                ip_address=discovered.ip_address,
                event_type="discovered",
                details=f"New device discovered: {discovered.hostname or discovered.mac_address}",
            )
            db.add(history)

            # Notify via WebSocket
            ws_manager = get_websocket_manager()
            await ws_manager.broadcast_device_discovered(device)

        return device

    def _guess_device_type(self, discovered: DiscoveredDevice) -> DeviceType:
        """Guess device type from hostname and vendor."""
        hostname = (discovered.hostname or "").lower()
        vendor = (discovered.vendor or "").lower()

        if any(kw in hostname for kw in ["iphone", "ipad", "android", "pixel", "galaxy"]):
            return DeviceType.PHONE
        if any(kw in hostname for kw in ["ipad", "tablet", "tab"]):
            return DeviceType.TABLET
        if any(kw in hostname for kw in ["tv", "smarttv", "roku", "firetv", "chromecast"]):
            return DeviceType.SMART_TV
        if any(kw in hostname for kw in ["printer", "print", "hp-", "canon-", "epson-", "brother-"]):
            return DeviceType.PRINTER
        if any(kw in hostname for kw in ["router", "gateway", "ap-", "access-point"]):
            return DeviceType.ROUTER
        if any(kw in hostname for kw in ["nas", "synology", "qnap", "freenas", "truenas"]):
            return DeviceType.NAS
        if any(kw in vendor for kw in ["raspberry", "arduino", "espressif", "sonoff", "shelly", "tuya"]):
            return DeviceType.IOT
        if any(kw in hostname for kw in ["ps4", "ps5", "xbox", "nintendo", "switch", "steamdeck"]):
            return DeviceType.GAMING
        if any(kw in hostname for kw in ["desktop", "pc-", "laptop", "macbook", "workstation"]):
            return DeviceType.COMPUTER

        return DeviceType.UNKNOWN

    async def mark_offline_devices(self, db: AsyncSession, online_macs: List[str]) -> None:
        """Mark devices not seen in scan as offline."""
        result = await db.execute(
            select(Device).where(Device.is_online == True)
        )
        online_devices = result.scalars().all()

        for device in online_devices:
            if device.mac_address not in online_macs:
                device.is_online = False
                history = DeviceHistory(
                    device_id=device.id,
                    ip_address=device.ip_address,
                    event_type="offline",
                    details="Device went offline",
                )
                db.add(history)

                # Notify via WebSocket
                ws_manager = get_websocket_manager()
                await ws_manager.broadcast_device_status(device.id, False)

    async def full_scan(self) -> Dict[str, Any]:
        """Perform a full network scan (ARP + service detection)."""
        self._is_scanning = True
        start_time = datetime.now(timezone.utc)
        stats = {
            "devices_found": 0,
            "new_devices": 0,
            "devices_online": 0,
            "scan_duration_seconds": 0,
        }

        try:
            async with get_session() as db:
                # ARP scan
                discovered = await self.arp_scan()
                stats["devices_found"] = len(discovered)

                online_macs = []
                for disc in discovered:
                    device = await self.update_device_from_discovery(db, disc)
                    online_macs.append(device.mac_address)
                    if not device.is_known:
                        stats["new_devices"] += 1
                    if device.is_online:
                        stats["devices_online"] += 1

                # Mark offline
                await self.mark_offline_devices(db, online_macs)
                # Commit happens automatically via get_session context manager

            # Service scan runs in its own session after the main scan commits
            asyncio.create_task(self._service_scan_authorized())

        finally:
            self._is_scanning = False
            stats["scan_duration_seconds"] = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

        return stats

    async def _service_scan_authorized(self) -> None:
        """Scan services on authorized devices (runs in its own session)."""
        try:
            async with get_session() as db:
                result = await db.execute(
                    select(Device).where(
                        Device.is_authorized == True,
                        Device.is_online == True,
                        Device.ip_address.isnot(None),
                    )
                )
                devices = result.scalars().all()

                for device in devices:
                    if device.ip_address:
                        scan_result = await self.nmap_scan(device.ip_address)
                        if scan_result.get("services"):
                            if scan_result.get("os_info"):
                                device.os_info = scan_result["os_info"]
                            history = DeviceHistory(
                                device_id=device.id,
                                ip_address=device.ip_address,
                                event_type="service_scan",
                                details=f"Found {len(scan_result['services'])} open ports",
                            )
                            db.add(history)
        except Exception as e:
            logger.error(f"Service scan failed: {e}")

    async def start_periodic_scans(self) -> None:
        """Start periodic network scans."""
        if self._scan_task and not self._scan_task.done():
            return

        async def scan_loop():
            while True:
                try:
                    await asyncio.sleep(self.settings.scan_interval_minutes * 60)
                    if not self._is_scanning:
                        await self.full_scan()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Periodic scan error: {e}")

        self._scan_task = asyncio.create_task(scan_loop())
        logger.info(f"Started periodic scans every {self.settings.scan_interval_minutes} minutes")

    async def stop_periodic_scans(self) -> None:
        """Stop periodic network scans."""
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            self._scan_task = None
            logger.info("Stopped periodic scans")


# Singleton instance
_network_scanner: Optional[NetworkScanner] = None


def get_network_scanner() -> NetworkScanner:
    """Get or create the network scanner singleton."""
    global _network_scanner
    if _network_scanner is None:
        _network_scanner = NetworkScanner()
    return _network_scanner