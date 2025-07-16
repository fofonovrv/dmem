#!/usr/bin/env python3
# dmem - Docker memory usage utility
# Copyright (c) 2025 Roman Fofonov
#
# This file is part of dmem and is licensed under the MIT License.
# See the LICENSE file or the following text for details:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the \"Software\"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import subprocess
import logging
import argparse
import shutil
from typing import List, Dict, Optional
import glob
import json
import csv
import sys


def setup_logger(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def check_dependencies() -> None:
    if not shutil.which("docker"):
        logging.error("Docker CLI not found in PATH.")
        exit(1)


def get_cgroup_version() -> int:
    if os.path.exists("/sys/fs/cgroup/cgroup.controllers"):
        logging.debug("Detected cgroup v2.")
        return 2
    else:
        logging.debug("Assuming cgroup v1.")
        return 1


def read_cgroup_file(path: str) -> Optional[int]:
    try:
        with open(path, "r") as f:
            content = f.read().strip()
            if content == "max":
                logging.debug(f"Read 'max' (unlimited) from {path}")
                return None
            value = int(content)
            logging.debug(f"Read {value} from {path}")
            return value
    except Exception as e:
        logging.warning(f"Failed to read {path}: {e}")
        return None


def read_cgroup_stat_file(path: str) -> Dict[str, int]:
    stats = {}
    try:
        with open(path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    key, value = parts
                    stats[key] = int(value)
    except Exception as e:
        logging.warning(f"Failed to read {path}: {e}")
    return stats


def get_memory_stats_v1(container_id: str) -> Dict[str, Optional[int]]:
    base_path = f"/sys/fs/cgroup/memory/docker/{container_id}"
    mem = read_cgroup_file(os.path.join(base_path, "memory.usage_in_bytes"))
    memsw = read_cgroup_file(os.path.join(base_path, "memory.memsw.usage_in_bytes"))
    mem_limit = read_cgroup_file(os.path.join(base_path, "memory.limit_in_bytes"))
    memsw_limit = read_cgroup_file(os.path.join(base_path, "memory.memsw.limit_in_bytes"))
    swap = memsw - mem if mem is not None and memsw is not None else None
    swap_limit = memsw_limit - mem_limit if memsw_limit is not None and mem_limit is not None else None
    stat = read_cgroup_stat_file(os.path.join(base_path, "memory.stat"))
    return {
        "ram": mem,
        "swap": swap,
        "limit": mem_limit,
        "swaplimit": swap_limit,
        "anon": stat.get("anon"),
        "file": stat.get("file"),
        "shmem": stat.get("shmem"),
        "rss": stat.get("rss"),
    }


def find_cgroup_path_v2(container_id: str) -> Optional[str]:
    """
    Найти путь cgroup v2 для контейнера (обычно через systemd).
    """
    pattern = f"/sys/fs/cgroup/**/docker-{container_id}.scope"
    matches = glob.glob(pattern, recursive=True)
    if matches:
        logging.debug(f"Found cgroup v2 path for {container_id}: {matches[0]}")
        return matches[0]
    logging.warning(f"Could not find cgroup v2 path for container {container_id}")
    return None


def get_memory_stats_v2(container_id: str) -> Dict[str, Optional[int]]:
    base_path = find_cgroup_path_v2(container_id)
    if not base_path:
        return {k: None for k in ["ram", "swap", "limit", "swaplimit", "anon", "file", "shmem", "rss"]}

    mem = read_cgroup_file(os.path.join(base_path, "memory.current"))
    swap = None
    swap_path = os.path.join(base_path, "memory.swap.current")
    if os.path.exists(swap_path):
        swap = read_cgroup_file(swap_path)
    mem_limit = read_cgroup_file(os.path.join(base_path, "memory.max"))
    swap_limit = None
    swap_limit_path = os.path.join(base_path, "memory.swap.max")
    if os.path.exists(swap_limit_path):
        swap_limit = read_cgroup_file(swap_limit_path)
    stat = read_cgroup_stat_file(os.path.join(base_path, "memory.stat"))
    return {
        "ram": mem,
        "swap": swap,
        "limit": mem_limit,
        "swaplimit": swap_limit,
        "anon": stat.get("anon"),
        "file": stat.get("file"),
        "shmem": stat.get("shmem"),
        "rss": stat.get("rss"),
    }


def get_all_containers() -> List[Dict[str, str]]:
    try:
        result = subprocess.run(
            ["docker", "ps", "--no-trunc", "--format", "{{.ID}} {{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        containers = []
        for line in result.stdout.strip().splitlines():
            if line:
                cid, name = line.strip().split(maxsplit=1)
                containers.append({"id": cid, "name": name})
        return containers
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running docker ps: {e.stderr.strip()}")
        exit(1)


def format_bytes(bytes_num: Optional[int]) -> str:
    if bytes_num is None:
        return "N/A"
    value = bytes_num
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value = value / 1024
    return f"{value:.1f} PB"


# Color helpers
RESET = "\033[0m"
BOLD = "\033[1m"
HEADER = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"

# Colorize a value based on thresholds
def colorize_value(value: str, raw: Optional[int], warn: int = 500*1024*1024, crit: int = 2*1024*1024*1024) -> str:
    if raw is None or value == "N/A":
        return value
    if raw >= crit:
        return f"{RED}{value}{RESET}"
    elif raw >= warn:
        return f"{YELLOW}{value}{RESET}"
    return value


def truncate_name(name: str, width: int = 30) -> str:
    return (name[:width-1] + '…') if len(name) > width else name


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Show Docker container memory usage (RAM and SWAP).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "-d", "--details", action="store_true",
        help="Show detailed output with all columns: Limit, SwapLimit, Anon, File, Shmem, RSS."
    )
    parser.add_argument(
        "--help-cols", action="store_true",
        help="Show description for each output column and exit."
    )
    parser.add_argument(
        "-f", "--filter", type=str, default=None,
        help="Show only containers whose name or ID contains the given substring."
    )
    parser.add_argument(
        "-o", "--output", type=str, choices=["table", "json", "csv"], default="table",
        help="Output format: table (default), json, or csv."
    )
    args = parser.parse_args()

    if getattr(args, 'help_cols', False):
        print("""
COLUMNS:
  CONTAINER   - Docker container name
  RAM Used    - Current RAM usage by container
  SWAP Used   - Current swap usage by container
  Limit       - RAM limit for container (if set)
  SwapLimit   - Swap limit for container (if set)
  Anon        - Anonymous memory (non-file-backed)
  File        - File/pagecache memory
  Shmem       - Shared memory
  RSS         - Resident Set Size (anon + part of file)
""")
        exit(0)

    def main(verbose: bool, details: bool, filter_str: Optional[str], output: str):
        setup_logger(verbose)
        check_dependencies()

        cgroup_version = get_cgroup_version()
        containers = get_all_containers()

        # Apply filter if specified
        if filter_str:
            containers = [c for c in containers if filter_str.lower() in c["name"].lower() or filter_str.lower() in c["id"].lower()]

        # Prepare data for output
        rows = []
        for container in containers:
            cid = container["id"][:12]  # Truncate to 12 characters like docker ps
            name = container["name"]
            if cgroup_version == 1:
                stats = get_memory_stats_v1(container["id"])
            else:
                stats = get_memory_stats_v2(container["id"])
            row = {
                "container": name,
                "id": cid,
                "ram": format_bytes(stats["ram"]),
                "ram_raw": stats["ram"],
                "swap": format_bytes(stats["swap"]),
                "swap_raw": stats["swap"],
            }
            if details:
                row.update({
                    "limit": format_bytes(stats["limit"]),
                    "swaplimit": format_bytes(stats["swaplimit"]),
                    "anon": format_bytes(stats["anon"]),
                    "file": format_bytes(stats["file"]),
                    "shmem": format_bytes(stats["shmem"]),
                    "rss": format_bytes(stats["rss"]),
                })
            rows.append(row)

        if output == "json":
            # Remove _raw fields for JSON output
            for row in rows:
                row.pop("ram_raw", None)
                row.pop("swap_raw", None)
            print(json.dumps(rows, indent=2))
            return
        elif output == "csv":
            if not rows:
                print("")
                return
            # Remove _raw fields for CSV output
            for row in rows:
                row.pop("ram_raw", None)
                row.pop("swap_raw", None)
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            return

        # Default: table output with color
        if details:
            print(f"{HEADER}{BOLD}{'CONTAINER':<31} {'ID':<12} {'RAM Used':>12} {'SWAP Used':>12} {'Limit':>12} {'SwapLimit':>12} {'Anon':>12} {'File':>12} {'Shmem':>12} {'RSS':>12}{RESET}")
            print(f"{HEADER}{'-' * 171}{RESET}")
        else:
            print(f"{HEADER}{BOLD}{'CONTAINER':<31} {'ID':<12} {'RAM Used':>12} {'SWAP Used':>12}{RESET}")
            print(f"{HEADER}{'-' * 67}{RESET}")
        for row in rows:
            # Truncate container name for table output
            container_str = truncate_name(row['container'], 30)
            # Format values to width first, then colorize
            ram_str = f"{row['ram']:>12}"
            swap_str = f"{row['swap']:>12}"
            ram = colorize_value(ram_str, row['ram_raw'])
            swap = colorize_value(swap_str, row['swap_raw'])
            if details:
                print(f"{container_str:<31} {row['id']:<12} {ram} {swap} {row['limit']:>12} {row['swaplimit']:>12} {row['anon']:>12} {row['file']:>12} {row['shmem']:>12} {row['rss']:>12}")
            else:
                print(f"{container_str:<31} {row['id']:<12} {ram} {swap}")

    main(verbose=args.verbose, details=getattr(args, 'details', False), filter_str=getattr(args, 'filter', None), output=getattr(args, 'output', 'table'))
