# Pantheon Setup & Congestion Control Evaluation

This guide documents the installation, setup, and experiment execution process of the [Pantheon](https://github.com/StanfordSNR/pantheon) framework, tested on **Ubuntu 18.04** in a **VirtualBox VM**, with manual resolution of Mahimahi and tunnel service issues.

---

## 📦 1. Clone the Repository and Initialize Submodules

```bash
git clone https://github.com/StanfordSNR/pantheon.git
cd pantheon
git submodule update --init --recursive
```

> If you see submodule errors (e.g., `proto-quic` failed), re-run the above command until all are cloned.

---

## 🐍 2. Install Python 2 and pip

```bash
sudo apt install python2 -y
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
sudo python2 get-pip.py
```

---

## 📚 3. Install Required Dependencies

```bash
sudo apt install -y \
  build-essential cmake python-is-python2 pkg-config \
  libboost-all-dev libprotobuf-dev protobuf-compiler \
  libgoogle-glog-dev libgflags-dev libpcap-dev \
  libssl-dev iproute2 net-tools iperf
```

---

## 💠 4. Install Mahimahi (PPA Broken in Ubuntu 18/20)

Instead of the broken PPA:
```bash
sudo apt install mahimahi
```

> ⚠️ The PPA `ppa:keithw/mahimahi` is deprecated; skip it.

---

## 🔧 5. Fix Tunnel Server Build (pantheon-tunnel)

```bash
cd third_party/pantheon-tunnel
./autogen.sh
./configure
make -j
sudo make install
```

> If `make` fails due to warnings treated as errors, upgrade your compiler:
```bash
sudo add-apt-repository ppa:ubuntu-toolchain-r/test
sudo apt update
sudo apt install gcc-11 g++-11
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100
```

---

## 🚀 6. Load Kernel Modules and Configure CC Support

```bash
sudo modprobe tcp_bbr
sudo modprobe tcp_vegas
sudo sysctl -w net.ipv4.tcp_allowed_congestion_control="reno cubic bbr vegas"
sudo sysctl -w net.core.default_qdisc=fq
sudo sysctl -w net.ipv4.ip_forward=1
```

---

## 🔀 7. Create Mahimahi Traces

```bash
seq 1 60 | awk '{print 50}' > src/experiments/50mbps.trace
seq 1 60 | awk '{print 1}' > src/experiments/1mbps.trace
```

---

## 🧪 8. Run Pantheon Experiments

### A. Low-Latency, High-Bandwidth (50 Mbps, 10ms RTT)

```bash
python2 src/experiments/test.py local \
  --schemes "vegas cubic bbr" \
  --run-times 1 \
  --runtime 60 \
  --data-dir result/50mbps_10ms \
  --uplink-trace src/experiments/50mbps.trace \
  --downlink-trace src/experiments/50mbps.trace \
  --prepend-mm-cmds "mm-delay 5"

python2 src/analysis/analyze.py --data-dir result/50mbps_10ms
```

### B. High-Latency, Constrained Bandwidth (1 Mbps, 200ms RTT)

```bash
python2 src/experiments/test.py local \
  --schemes "vegas cubic bbr" \
  --run-times 1 \
  --runtime 60 \
  --data-dir result/1mbps_200ms \
  --uplink-trace src/experiments/1mbps.trace \
  --downlink-trace src/experiments/1mbps.trace \
  --prepend-mm-cmds "mm-delay 100"

python2 src/analysis/analyze.py --data-dir result/1mbps_200ms
```

---

## 🛠 9. Troubleshooting Tips

- **Tunnel Errors / Timeout**:
  - Ensure `mm-tunnelserver` is installed:
    ```bash
    which mm-tunnelserver
    ```
    If missing, rebuild and install `pantheon-tunnel`.

- **Tunnel Connection Timeout**:
  - Check permissions:
    ```bash
    ls -l /usr/local/bin/mm-tunnelserver
    ```
    Should be `-rwsr-xr-x root root`.

- **If Mahimahi commands fail**:
  ```bash
  sudo sysctl -w net.ipv4.ip_forward=1
  ```

- **Export Mahimahi path if needed**:
  ```bash
  export MAHIMAHI_BASE=/usr/bin
  ```

---

## 📊 10. Results & Outputs

Each experiment logs:
- `*.log` files in `result/<experiment_name>/`
- Throughput, RTT, and loss graphs
- Auto-generated PDF report (optional, if LaTeX is installed)

---

## ✅ Final Notes

- All tests ran successfully with **Cubic**, **BBR**, and **Vegas**.
- Graphs were generated using Pantheon’s built-in tools.
- All custom traces are 60s long to simulate 1-minute traffic runs.
- Logs were saved and can be analyzed or committed to a GitHub repo.

---

⏳ **Last verified:** April 24, 2025


