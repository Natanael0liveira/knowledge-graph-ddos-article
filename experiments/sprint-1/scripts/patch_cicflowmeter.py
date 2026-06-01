#!/usr/bin/env python3
"""Apply runtime patches to cicflowmeter 0.2.0 + scapy 2.5.0.

Three bugs fixed:
1. flow_bytes.py::get_min_forward_header_bytes — min() on empty forward
   list raises ValueError, killing the AsyncSniffer thread mid-PCAP.
2. packet_length.py::get_min_header — same min()-empty pattern.
3. flow_session.py::garbage_collect — any feature-extraction exception
   propagates and kills the thread; wrap output write defensively.

Idempotent: if the patch markers are already present, skips.
"""
import sys
from pathlib import Path

import cicflowmeter

PKG_ROOT = Path(cicflowmeter.__file__).parent


def patch(file_path: Path, old: str, new: str, marker: str) -> bool:
    """Replace ``old`` with ``new`` in file iff ``marker`` not yet present.

    Returns True if a write occurred.
    """
    txt = file_path.read_text()
    if marker in txt:
        print(f"  [skip] {file_path.name} already patched")
        return False
    if old not in txt:
        print(f"  [WARN] {file_path.name}: expected snippet not found — skipping")
        return False
    file_path.write_text(txt.replace(old, new))
    print(f"  [ok]   {file_path.name} patched")
    return True


def main() -> int:
    print("==> Patching cicflowmeter 0.2.0 (idempotent)...")

    fb = PKG_ROOT / "features" / "flow_bytes.py"
    patch(
        fb,
        old=(
            "        if not self.flow.packets:\n"
            "            return 0\n"
            "\n"
            "        return min(\n"
            "            self._header_size(packet)\n"
            "            for packet, direction in self.flow.packets\n"
            "            if direction == PacketDirection.FORWARD\n"
            "        )"
        ),
        new=(
            "        if not self.flow.packets:\n"
            "            return 0\n"
            "\n"
            "        fwd_sizes = [\n"
            "            self._header_size(packet)\n"
            "            for packet, direction in self.flow.packets\n"
            "            if direction == PacketDirection.FORWARD\n"
            "        ]\n"
            "        return min(fwd_sizes) if fwd_sizes else 0"
        ),
        marker="fwd_sizes = [",
    )

    pl = PKG_ROOT / "features" / "packet_length.py"
    patch(
        pl,
        old=(
            "    def get_min_header(self, packet_direction=None) -> int:\n"
            '        """Min the summary header lengths.\n'
            "\n"
            "        Returns:\n"
            "            packet_lengths (List[int]):\n"
            "\n"
            '        """\n'
            "        return min(self.get_header_length(packet_direction))"
        ),
        new=(
            "    def get_min_header(self, packet_direction=None) -> int:\n"
            '        """Min the summary header lengths.\n'
            "\n"
            "        Returns:\n"
            "            packet_lengths (List[int]):\n"
            "\n"
            '        """\n'
            "        try:\n"
            "            return min(self.get_header_length(packet_direction))\n"
            "        except ValueError:\n"
            "            return 0"
        ),
        marker="try:\n            return min(self.get_header_length",
    )

    fs = PKG_ROOT / "flow_session.py"
    patch(
        fs,
        old=(
            "            self.output_writer.write(flow.get_data(self.fields))\n"
            "            del self.flows[k]"
        ),
        new=(
            "            try:\n"
            "                self.output_writer.write(flow.get_data(self.fields))\n"
            "            except Exception as exc:\n"
            "                self.logger.warning(f\"Skipping flow {k}: {exc}\")\n"
            "            del self.flows[k]"
        ),
        marker='self.logger.warning(f"Skipping flow',
    )

    print("==> Patches done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
