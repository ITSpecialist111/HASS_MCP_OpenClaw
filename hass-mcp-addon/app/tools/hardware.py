"""§53 Hardware-layer control (serial, GPIO, I2C/SPI, BT, IR, RTL-SDR, PDU)."""
from __future__ import annotations

import base64
from typing import Any

import httpx

from .. import shell as _shell
from ._helpers import tool


def register(mcp) -> int:

    @tool(mcp)
    async def serial_open_send(device: str, baud: int = 115200,
                                 write_b64: str | None = None,
                                 read_seconds: float = 2.0) -> Any:
        """§53 Open /dev/ttyUSB*, optionally write bytes, then read for N seconds."""
        try:
            import serial
        except ImportError:
            return {"error": "pyserial not installed"}
        with serial.Serial(device, baud, timeout=read_seconds) as ser:
            if write_b64:
                ser.write(base64.b64decode(write_b64))
                ser.flush()
            data = ser.read(65536)
        return {"device": device, "bytes_read": len(data),
                "data_b64": base64.b64encode(data).decode()}

    @tool(mcp)
    async def serial_list_ports() -> Any:
        """§53 List available serial ports."""
        try:
            from serial.tools import list_ports
            return [{"device": p.device, "description": p.description,
                      "hwid": p.hwid} for p in list_ports.comports()]
        except ImportError:
            return await _shell.shell_exec(
                "ls -l /dev/serial/by-id/ /dev/ttyUSB* /dev/ttyACM* 2>/dev/null",
                timeout=5.0)

    @tool(mcp)
    async def gpio_write(pin: int, value: int) -> Any:
        """§53 RPi GPIO write (sysfs)."""
        return await _shell.shell_exec(
            f"echo {pin} > /sys/class/gpio/export 2>/dev/null; "
            f"echo out > /sys/class/gpio/gpio{pin}/direction; "
            f"echo {value} > /sys/class/gpio/gpio{pin}/value", timeout=5.0)

    @tool(mcp)
    async def gpio_read(pin: int) -> Any:
        """§53 RPi GPIO read (sysfs)."""
        return await _shell.shell_exec(
            f"echo {pin} > /sys/class/gpio/export 2>/dev/null; "
            f"echo in > /sys/class/gpio/gpio{pin}/direction; "
            f"cat /sys/class/gpio/gpio{pin}/value", timeout=5.0)

    @tool(mcp)
    async def i2c_scan(bus: int = 1) -> Any:
        """§53 i2cdetect -y <bus>."""
        return await _shell.shell_exec(f"i2cdetect -y {bus}", timeout=10.0)

    @tool(mcp)
    async def i2c_read(bus: int, address: int, register: int,
                         length: int = 1) -> Any:
        """§53 i2cget loop."""
        out = []
        for i in range(length):
            r = await _shell.shell_exec(
                f"i2cget -y {bus} {hex(address)} {hex(register + i)}",
                timeout=5.0)
            out.append(r.get("stdout", "").strip())
        return {"bytes": out}

    @tool(mcp)
    async def i2c_write(bus: int, address: int, register: int,
                          value: int) -> Any:
        """§53 i2cset."""
        return await _shell.shell_exec(
            f"i2cset -y {bus} {hex(address)} {hex(register)} {hex(value)}",
            timeout=5.0)

    @tool(mcp)
    async def spi_xfer(device: str, write_b64: str, speed: int = 500000) -> Any:
        """§53 spidev transfer (requires python spidev)."""
        try:
            import spidev
        except ImportError:
            return {"error": "spidev not installed"}
        bus, dev = (int(x) for x in device.replace("/dev/spidev", "").split("."))
        s = spidev.SpiDev(); s.open(bus, dev); s.max_speed_hz = speed
        try:
            data = s.xfer2(list(base64.b64decode(write_b64)))
        finally:
            s.close()
        return {"data_b64": base64.b64encode(bytes(data)).decode()}

    @tool(mcp)
    async def bluetooth_command(command: str) -> Any:
        """§53 bluetoothctl <command> e.g. 'scan on', 'pair AA:BB:..', 'remove ...'."""
        return await _shell.shell_exec(
            f"echo -e {command!r} | timeout 15 bluetoothctl", timeout=20.0)

    @tool(mcp)
    async def bluetooth_gatt_read(mac: str, handle: str = "0x0001") -> Any:
        """§53 gatttool char-read-hnd."""
        return await _shell.shell_exec(
            f"timeout 10 gatttool -b {mac} --char-read --handle={handle}",
            timeout=15.0)

    @tool(mcp)
    async def infrared_send(remote: str, button: str) -> Any:
        """§53 LIRC: irsend SEND_ONCE <remote> <button>."""
        return await _shell.shell_exec(
            f"irsend SEND_ONCE {remote} {button}", timeout=10.0)

    @tool(mcp)
    async def rtl_sdr_capture(frequency_hz: int, sample_rate: int = 2048000,
                                seconds: float = 5.0,
                                output_path: str = "/share/sdr_capture.cu8") -> Any:
        """§53 rtl_sdr capture."""
        n = int(sample_rate * seconds)
        return await _shell.shell_exec(
            f"timeout {seconds + 5} rtl_sdr -f {frequency_hz} "
            f"-s {sample_rate} -n {n} {output_path}",
            timeout=seconds + 30)

    @tool(mcp)
    async def rtl_433_decode(frequency_hz: int = 433920000,
                               seconds: float = 30.0) -> Any:
        """§53 rtl_433 capture decoded JSON."""
        return await _shell.shell_exec(
            f"timeout {seconds} rtl_433 -f {frequency_hz} -F json",
            timeout=seconds + 10)

    @tool(mcp)
    async def usb_hubctl(location: str, port: int, action: str = "cycle") -> Any:
        """§53 uhubctl power-cycle a USB port. action ∈ on|off|cycle."""
        flag = {"on": "1", "off": "0", "cycle": "2"}.get(action, "2")
        return await _shell.shell_exec(
            f"uhubctl -l {location} -p {port} -a {flag}", timeout=20.0)

    @tool(mcp)
    async def pdu_outlet_control(base_url: str, outlet: int, action: str,
                                   auth_user: str | None = None,
                                   auth_pass: str | None = None,
                                   token: str | None = None) -> Any:
        """§53 Generic smart-PDU REST (APC NMC, Tasmota, Shelly, EatonE)."""
        method = "POST"
        url = f"{base_url.rstrip('/')}/outlet/{outlet}/{action}"
        async with httpx.AsyncClient(timeout=30.0, verify=False) as c:
            kw: dict = {}
            if token: kw["headers"] = {"Authorization": f"Bearer {token}"}
            elif auth_user and auth_pass: kw["auth"] = (auth_user, auth_pass)
            r = await c.request(method, url, **kw)
            try: body = r.json()
            except Exception: body = r.text
        return {"status_code": r.status_code, "body": body}

    @tool(mcp)
    async def acoustic_play(media_player: str, audio_url: str) -> Any:
        """§53 Pipe arbitrary audio URL to any speaker (HA media_player.play_media)."""
        from ..ws_client import get_ws
        return await get_ws().call("call_service", domain="media_player",
                                    service="play_media",
                                    service_data={"entity_id": media_player,
                                                  "media_content_id": audio_url,
                                                  "media_content_type": "music"})

    return 16
