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

## Why dmem?

Standard Docker commands like `docker stats` provide a good overview of container resource usage, but they often fall short when you need precise details about **SWAP memory consumption**. For system administrators and DevOps engineers, understanding swap usage is crucial for:

* **Troubleshooting performance issues:** High swap usage can indicate memory pressure and degrade application performance.
* **Optimizing resource allocation:** Accurately assessing memory needs helps prevent over-provisioning or under-provisioning resources.
* **Identifying memory leaks:** Unexpected swap growth can signal a memory leak within a containerized application.

`dmem` bridges this gap by directly interacting with Linux cgroups (where container resource statistics are maintained), extracting and presenting comprehensive memory data, including a dedicated SWAP usage column, in an easily digestible format.

## How it works?

`dmem` leverages the power of **Linux cgroups** to gather precise memory statistics. When Docker (or any container runtime) creates a container, it also sets up a dedicated cgroup for it. Inside these cgroups, the kernel maintains detailed accounting of resource usage.

`dmem` performs the following steps:
1.  It identifies all running Docker containers.
2.  For each container, it determines its corresponding cgroup path on the host system (supporting both v1 and v2 cgroup hierarchies).
3.  It then reads specific memory-related files within that cgroup (e.g., `memory.usage_in_bytes`, `memory.swap.current`, `memory.memsw.usage_in_bytes`) to collect accurate RAM and SWAP usage data.
4.  Finally, it processes this raw data into human-readable formats, including a clear distinction between RAM and SWAP consumption.


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


## Tested On

dmem has been tested on the following environments:

- Arch Linux ARM (cgroup v2), Python 3.13.5, Docxker 28.2.0
- Arch Linux (cgroup v2), Python 3.13.5, Docker 28.3.2
- Ubuntu 22.04.2 LTS (cgroup v2), Python 3.10.6, Docker 24.0.2
- CentOS 7 (cgroup v1), Python 3.6.8, Docker 26.1.4

## Contributing

I welcome contributions to dmem! If you have ideas for new features, bug fixes, or improvements, please feel free to:

1. Open an issue: Describe the bug you found or the feature you'd like to see.
2. Submit a Pull Request: If you've implemented a change, submit a PR with a clear description of your modifications and tests if applicable.  

Please ensure your code adheres to a consistent style and includes appropriate comments.

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.


## Contact

For any questions, suggestions, or feedback, you can reach out to the maintainer:
- GitHub Issues: https://github.com/fofonovrv/dmem/issues
- fofonovrv@gmail.com
