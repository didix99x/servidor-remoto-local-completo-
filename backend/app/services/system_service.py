"""
System information service - CPU, RAM, disk, network traffic.
"""
import asyncio
import platform
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import psutil

logger = logging.getLogger(__name__)

_start_time = time.time()


def get_system_info() -> Dict[str, Any]:
    """Get current system information snapshot."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/") if platform.system() != "Windows" else psutil.disk_usage("C:\\")

    net_io = psutil.net_io_counters()

    return {
        "cpu_percent": cpu_percent,
        "cpu_count": psutil.cpu_count(),
        "memory_percent": memory.percent,
        "memory_total_gb": round(memory.total / (1024 ** 3), 2),
        "memory_used_gb": round(memory.used / (1024 ** 3), 2),
        "memory_available_gb": round(memory.available / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "disk_total_gb": round(disk.total / (1024 ** 3), 2),
        "disk_used_gb": round(disk.used / (1024 ** 3), 2),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "net_bytes_sent": net_io.bytes_sent,
        "net_bytes_recv": net_io.bytes_recv,
        "net_packets_sent": net_io.packets_sent,
        "net_packets_recv": net_io.packets_recv,
        "uptime_seconds": time.time() - _start_time,
        "platform": platform.system(),
        "python_version": sys.version.split()[0],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class SystemMonitor:
    """Periodic system stats broadcaster via WebSocket."""

    def __init__(self, interval_seconds: int = 3):
        self.interval = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._prev_net = psutil.net_io_counters()
        self._prev_time = time.time()

    def get_network_speed(self) -> Dict[str, float]:
        """Calculate current network speed in bytes/sec."""
        current_net = psutil.net_io_counters()
        current_time = time.time()
        elapsed = current_time - self._prev_time

        if elapsed <= 0:
            return {"upload_bps": 0.0, "download_bps": 0.0}

        upload = (current_net.bytes_sent - self._prev_net.bytes_sent) / elapsed
        download = (current_net.bytes_recv - self._prev_net.bytes_recv) / elapsed

        self._prev_net = current_net
        self._prev_time = current_time

        return {
            "upload_bps": max(0.0, upload),
            "download_bps": max(0.0, download),
        }

    async def start(self) -> None:
        if self._task and not self._task.done():
            return

        async def monitor_loop():
            from app.services.websocket_manager import get_websocket_manager
            ws = get_websocket_manager()
            while True:
                try:
                    stats = get_system_info()
                    net_speed = self.get_network_speed()
                    stats.update(net_speed)
                    if ws.get_connection_count() > 0:
                        await ws.broadcast_system_stats(stats)
                    await asyncio.sleep(self.interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"System monitor error: {e}")
                    await asyncio.sleep(self.interval)

        self._task = asyncio.create_task(monitor_loop())
        logger.info(f"System monitor started (interval={self.interval}s)")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    global _monitor
    if _monitor is None:
        _monitor = SystemMonitor()
    return _monitor
