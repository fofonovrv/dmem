# dmem

A simple yet powerful Python utility to display memory (RAM and SWAP) usage for all running Docker containers on a Linux system. It supports both cgroup v1 and v2, providing detailed memory statistics per container.

## Features
- **Lists RAM and SWAP usage** for each Docker container
- **Supports both cgroup v1 and v2** (works on modern and legacy Linux systems)
- **Shows memory limits and detailed stats** (with `--details`)
- **Human-readable, colorized output** for better readability
- **Filter by container name or ID** (`-f`/`--filter`)
- **Output in JSON or CSV for automation** (`-o json`/`-o csv`)
- **Container ID is truncated to 12 characters** (like `docker ps`)
- **Verbose/debug mode** for troubleshooting
- **No dependencies except Docker and Python 3**

## Usage
```bash
python3 dmem.py [OPTIONS]
```

### Options
- `-v`, `--verbose`      Enable debug logging
- `-d`, `--details`      Show detailed output (limits, anon, file, shmem, RSS)
- `--help-cols`          Show description for each output column and exit
- `-f`, `--filter`       Show only containers whose name or ID contains the given substring
- `-o`, `--output`       Output format: `table` (default), `json`, or `csv`

### Example Output (Table, Colorized)
```
CONTAINER                 ID           RAM Used     SWAP Used
--------------------------------------------------------------------
my_app_container          123456789abc  120.3 MB      10.0 MB
another_container         abcdef123456  512.0 MB      N/A
```

With `--details`:
```
CONTAINER                 ID           RAM Used     SWAP Used        Limit    SwapLimit         Anon         File        Shmem          RSS
------------------------------------------------------------------------------------------------------------------------------------------
my_app_container          123456789abc  120.3 MB      10.0 MB    2.0 GB     1.0 GB     100.0 MB     10.0 MB      5.0 MB    110.0 MB
```

### Filtering Example
```bash
python3 dmem.py --filter nginx
```

### JSON Output Example
```bash
python3 dmem.py -o json
```

### CSV Output Example
```bash
python3 dmem.py -o csv
```

## Installation
Just copy `dmem.py` to any directory in your `$PATH` and make it executable:
```bash
chmod +x dmem.py
sudo mv dmem.py /usr/local/bin/dmem
```

Or download directly with curl:
```bash
curl -L https://raw.githubusercontent.com/fofonovrv/dmem/main/dmem.py -o dmem
chmod +x dmem
sudo mv dmem /usr/local/bin/dmem
```

## Requirements
- Python 3.6+
- Docker CLI
- Linux with cgroup support (v1 or v2)

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
