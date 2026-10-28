#!/usr/bin/env python3
"""Install secretd 1.27.2 and bring up a secret-4 node."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

VERSION = "1.27.2"
CHAIN_ID = "secret-4"
RPC = "https://rpc.secret.mainnet.secret3.dev"
RELEASE = "https://github.com/Secret3dev/SecretNetwork/releases/download/v1.27.2"
# tx register auth: --gas 700000 --gas-prices 0.1uscrt → 0.07 SCRT (70000 uscrt).
REGISTER_MIN_USCRT = 70_000
DEB_SHA256 = {
    "22.04": "ffcca0fe04422228ae92b0bb216808a0eafa1030a7073d1bf1ca347a0781fcbb",
    "24.04": "f90e7104d6308d491c9cfdb691672302b17b3364c3b355962479adc46da3d903",
}
SGX_QCNL_CONF = (
    '{"pccs_url":"https://api.trustedservices.intel.com/sgx/certification/v4/",'
    '"use_secure_cert":true,"retry_times":6,"retry_delay":10,'
    '"pck_cache_expire_hours":168,"verify_collateral_cache_expire_hours":168,'
    '"local_cache_only":false}'
)
AZURE_THIM_QCNL_CONF = (
    '{"pccs_url":"https://global.acccache.azure.net/sgx/certification/v4/",'
    '"use_secure_cert":true,'
    '"collateral_service":"https://api.trustedservices.intel.com/sgx/certification/v4/",'
    '"pccs_api_version":"3.1","retry_times":6,"retry_delay":5,'
    '"local_pck_url":"http://169.254.169.254/metadata/THIM/sgx/certification/v4/",'
    '"pck_cache_expire_hours":48,"verify_collateral_cache_expire_hours":48,'
    '"custom_request_options":{"get_cert":{"headers":{"metadata":"true"},'
    '"params":{"api-version":"2021-07-22-preview"}}}}'
)
SGX_APT_PACKAGES = [
    "libsgx-aesm-launch-plugin",
    "libsgx-enclave-common",
    "libsgx-epid",
    "libsgx-launch",
    "libsgx-quote-ex",
    "libsgx-uae-service",
    "libsgx-qe3-logic",
    "libsgx-pce-logic",
    "libsgx-aesm-pce-plugin",
    "libsgx-dcap-ql",
    "libsgx-dcap-quote-verify",
    "libsgx-urts",
    "sgx-aesm-service",
    "libsgx-aesm-ecdsa-plugin",
    "libsgx-aesm-quote-ex-plugin",
    "libsgx-ae-qve",
    "libsgx-dcap-default-qpl",
]
SGX_UDEV_RULES = """SUBSYSTEM=="misc", KERNEL=="sgx_enclave", MODE="0660", GROUP="sgx"
SUBSYSTEM=="misc", KERNEL=="sgx_provision", MODE="0660", GROUP="sgx_prv"
"""
# cosmos-sdk v0.50.14-secret.12 client/input.GetPassword, and bcrypt's limit.
MIN_PASSPHRASE = 8
MAX_PASSPHRASE = 72

HOME = Path.home() / ".secretd"
PASSWORD = ""


class Stop(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def die(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def prompt(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print("Enter a value.", file=sys.stderr)


def prompt_yes_no(label: str) -> bool:
    while True:
        value = input(label).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Answer yes or no.", file=sys.stderr)


def prompt_prune() -> str:
    while True:
        value = input("Prune setting (default, nothing, everything): ").strip().lower()
        if value in {"default", "nothing", "everything"}:
            return value
        if value == "archive":
            return "nothing"
        print("Choose default, nothing, or everything.", file=sys.stderr)


def prompt_password() -> str:
    while True:
        value = getpass.getpass("Keyring password: ")
        size = len(value.encode())
        if size < MIN_PASSPHRASE:
            print(
                f"Use at least {MIN_PASSPHRASE} characters.",
                file=sys.stderr,
            )
            continue
        if size > MAX_PASSPHRASE:
            print(
                f"Use at most {MAX_PASSPHRASE} bytes.",
                file=sys.stderr,
            )
            continue
        if "\n" in value or "\x00" in value:
            print("The passphrase is one line.", file=sys.stderr)
            continue
        return value


def key_exists(name: str) -> bool:
    # File backend item "<name>.info"; "/" in the name is percent-encoded.
    return (HOME / "keyring-file" / (name.replace("/", "%2F") + ".info")).is_file()


def keyhash_exists() -> bool:
    return (HOME / "keyring-file" / "keyhash").is_file()


def check_host() -> str:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        die("Run this as the account that will own the node, not as root.")
    if os.uname().machine != "x86_64":
        die("This package is amd64.")
    info: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        info[key] = value.strip().strip('"')
    if info.get("ID") != "ubuntu" or info.get("VERSION_ID") not in DEB_SHA256:
        die("Ubuntu 22.04 or 24.04 is required.")
    if not sys.stdin.isatty():
        die("Run this in a terminal. It asks for the moniker, key, and passphrase on this machine.")
    resume = (HOME / "config" / "genesis.json").is_file()
    return info["VERSION_ID"], resume


def run(
    args: list[str],
    *,
    password_lines: int = 0,
    cwd: Path | None = None,
    suppress_stdout: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    shown = list(args)
    if args[:2] == ["secretd", "configure-secret"] and len(shown) >= 4:
        shown[3] = "<seed>"
    print("+ " + " ".join(shlex.quote(part) for part in shown), file=sys.stderr)
    payload = None
    if password_lines:
        payload = (PASSWORD + "\n") * password_lines
    proc = subprocess.run(
        args,
        input=payload,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd) if cwd else None,
    )
    if proc.stdout and not suppress_stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "\n", file=sys.stderr)
    if check and proc.returncode != 0:
        raise Stop(f"Command failed ({proc.returncode}): {' '.join(shlex.quote(part) for part in shown)}")
    return proc


def sudo(args: list[str]) -> None:
    run(["sudo", *args])


def read_os_release() -> dict[str, str]:
    info: dict[str, str] = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        info[key] = value.strip().strip('"')
    return info


def ubuntu_codename(version_id: str) -> str:
    codename = read_os_release().get("VERSION_CODENAME", "")
    if codename:
        return codename
    return {"22.04": "jammy", "24.04": "noble"}.get(version_id, "")


def node_user() -> str:
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
    if user:
        return user
    raise Stop("Cannot determine the node user.")


def install_packages() -> None:
    sudo(["apt-get", "update"])
    sudo(
        [
            "apt-get",
            "install",
            "-y",
            "curl",
            "ca-certificates",
            "jq",
            "zstd",
            "tar",
            "libsnappy1v5",
            "gpg",
        ]
    )


def azure_dcsv3_vm() -> bool:
    try:
        proc = subprocess.run(
            [
                "curl",
                "-fsS",
                "--noproxy",
                "*",
                "--connect-timeout",
                "1",
                "-H",
                "Metadata:true",
                "http://169.254.169.254/metadata/instance/compute/vmSize"
                "?api-version=2021-02-01&format=text",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if proc.returncode != 0:
        return False
    size = proc.stdout.strip().lower()
    if not size.startswith("standard_dc"):
        return False
    return bool(re.search(r"dc\d+s_v3", size) or re.search(r"dc\d+ds_v3", size))


def sgx_dcap_libraries_present() -> bool:
    proc = subprocess.run(
        ["ldconfig", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    if proc.returncode != 0:
        return False
    listed = proc.stdout
    return all(
        name in listed
        for name in (
            "libsgx_urts.so.2",
            "libsgx_dcap_ql.so.1",
            "libsgx_dcap_quoteverify.so.1",
        )
    )


def install_intel_sgx_repo(codename: str) -> None:
    if sgx_dcap_libraries_present():
        return
    keyring = "/usr/share/keyrings/intel-sgx-archive-keyring.gpg"
    if not Path(keyring).is_file():
        sudo(
            [
                "bash",
                "-c",
                "curl -fsSL https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key "
                f"| gpg --dearmor -o {keyring}",
            ]
        )
    list_path = Path("/tmp/intel-sgx.list")
    list_path.write_text(
        f"deb [signed-by={keyring}] "
        f"https://download.01.org/intel-sgx/sgx_repo/ubuntu {codename} main\n"
    )
    sudo(["cp", str(list_path), "/etc/apt/sources.list.d/intel-sgx.list"])
    sudo(["apt-get", "update"])
    sudo(["apt-get", "install", "-y", *SGX_APT_PACKAGES])


def ensure_aesmd() -> None:
    sudo(["systemctl", "enable", "--now", "aesmd"])
    sudo(["systemctl", "restart", "aesmd"])
    time.sleep(2)
    proc = subprocess.run(
        ["systemctl", "is-active", "aesmd"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.stdout.strip() != "active":
        raise Stop("aesmd is not active after enable and restart.")


def write_sgx_qcnl_config(content: str | None = None) -> None:
    temp = Path("/tmp/sgx_default_qcnl.conf")
    temp.write_text((content if content is not None else SGX_QCNL_CONF) + "\n")
    sudo(["cp", str(temp), "/etc/sgx_default_qcnl.conf"])
    sudo(["chmod", "644", "/etc/sgx_default_qcnl.conf"])


def ensure_group(name: str) -> None:
    proc = subprocess.run(
        ["getent", "group", name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        sudo(["groupadd", name])


def configure_sgx_device_access(user: str) -> None:
    ensure_group("sgx")
    ensure_group("sgx_prv")
    sudo(["usermod", "-aG", "sgx", user])
    sudo(["usermod", "-aG", "sgx_prv", user])
    rules = Path("/tmp/99-sgx-permissions.rules")
    rules.write_text(SGX_UDEV_RULES)
    sudo(["cp", str(rules), "/etc/udev/rules.d/99-sgx-permissions.rules"])
    sudo(["udevadm", "control", "--reload-rules"])
    sudo(["udevadm", "trigger"])
    for dev, group in (("/dev/sgx_enclave", "sgx"), ("/dev/sgx_provision", "sgx_prv")):
        if not Path(dev).exists():
            raise Stop(f"{dev} is missing. Enable SGX in firmware or use an SGX-capable host.")
        sudo(["chgrp", group, dev])
        sudo(["chmod", "0660", dev])


def setup_sgx_runtime(_version_id: str) -> None:
    azure_sgx = azure_dcsv3_vm()
    if azure_sgx:
        write_sgx_qcnl_config(AZURE_THIM_QCNL_CONF)
    else:
        write_sgx_qcnl_config()
    ensure_aesmd()
    configure_sgx_device_access(node_user())


def run_init_enclave() -> None:
    inner = shlex.quote("secretd init-enclave")
    run(["sg", "sgx", "-c", f"sg sgx_prv -c {inner}"])


def install_deb(version_id: str) -> None:
    name = f"secretnetwork_{VERSION}_MAINNET_goleveldb_amd64_ubuntu-{version_id}.deb"
    dest = Path("/tmp") / name
    run(["curl", "-fL", "-o", str(dest), f"{RELEASE}/{name}"])
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    if digest != DEB_SHA256[version_id]:
        dest.unlink(missing_ok=True)
        die(f"SHA-256 mismatch for {name}.")
    sudo(["dpkg", "-i", str(dest)])
    fix_opt_secret_permissions()
    os.environ["PATH"] = "/usr/local/bin:" + os.environ.get("PATH", "")
    proc = run(["secretd", "version"], suppress_stdout=True)
    first = proc.stdout.splitlines()[0].strip() if proc.stdout else ""
    if first != VERSION:
        die(f"secretd version is {first!r}, expected {VERSION}.")


def fix_opt_secret_permissions() -> None:
    unit = os.environ.get("SUDO_USER") or os.environ.get("USER") or ""
    if not unit:
        raise Stop("Cannot determine the account that owns /opt/secret.")
    sudo(["chown", "-R", f"{unit}:{unit}", "/opt/secret", "/opt/secret/.sgx_secrets"])
    sudo(
        [
            "find",
            "/opt/secret",
            "/opt/secret/.sgx_secrets",
            "-type",
            "d",
            "-exec",
            "chmod",
            "750",
            "{}",
            ";",
        ]
    )
    sudo(
        [
            "find",
            "/opt/secret",
            "/opt/secret/.sgx_secrets",
            "-type",
            "f",
            "-exec",
            "chmod",
            "600",
            "{}",
            ";",
        ]
    )


def write_client_config() -> None:
    path = HOME / "config" / "client.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            "\n".join(
                [
                    'chain-id = "secret-4"',
                    'keyring-backend = "file"',
                    'output = "text"',
                    'node = "tcp://localhost:26657"',
                    'broadcast-mode = "sync"',
                    "",
                ]
            )
        )
        path.chmod(0o600)
        return
    set_toml(path, "", "keyring-backend", '"file"')
    set_toml(path, "", "chain-id", '"secret-4"')


def has_seed() -> bool:
    node = HOME / ".node"
    for name in ("new_seed.json", "seed.json"):
        path = node / name
        if path.is_file() and path.stat().st_size > 0:
            return True
    return False


def key_address(name: str) -> str:
    proc = run(
        ["secretd", "keys", "show", name, "-a", "--keyring-backend", "file"],
        password_lines=1,
        suppress_stdout=True,
    )
    addr = (proc.stdout or "").strip()
    if not addr:
        raise Stop("Could not read the key address.")
    return addr


def ensure_funds(name: str) -> None:
    addr = key_address(name)
    proc = run(
        [
            "secretd",
            "query",
            "bank",
            "balances",
            addr,
            "--node",
            RPC,
            "--output",
            "json",
        ],
        suppress_stdout=True,
        check=False,
    )
    if proc.returncode != 0:
        err = ((proc.stderr or "") + (proc.stdout or "")).strip()
        die(err if err else f"Could not query balance for {addr}. Stopped.")
    try:
        body = json_object(proc.stdout or "")
    except Stop as exc:
        die(f"{exc.message} Stopped.")
    total = 0
    for coin in body.get("balances") or []:
        if isinstance(coin, dict) and coin.get("denom") in {"uscrt", "uuscr"}:
            total += int(coin.get("amount") or 0)
    if total < REGISTER_MIN_USCRT:
        die(f"Balance is under 0.07 SCRT. Send at least 0.07 SCRT to {addr}. Stopped.")


def existing_pruning() -> str | None:
    app = HOME / "config" / "app.toml"
    if not app.is_file():
        return None
    for line in app.read_text().splitlines():
        match = re.match(r'^\s*pruning\s*=\s*"([^"]+)"\s*(?:#.*)?$', line)
        if match:
            return match.group(1)
    return None


def local_rpc_responds() -> bool:
    proc = subprocess.run(
        ["curl", "-fsS", "--max-time", "3", "http://127.0.0.1:26657/status"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc.returncode == 0


def has_blockstore() -> bool:
    data = HOME / "data"
    if not data.is_dir():
        return False
    for name in ("application.db", "blockstore.db"):
        if (data / name).exists():
            return True
    return False


def run_restore_if_needed() -> bool:
    if has_blockstore() and not local_rpc_responds():
        print(
            "Local block data is present and the node is not running; skipping restore.",
            file=sys.stderr,
        )
        return False
    restore_snapshot()
    return True


def ensure_key(name: str) -> None:
    if key_exists(name):
        print(f"Using existing key {name}.")
        return
    # New keyring: newRealPrompt reads the passphrase and then "Re-enter".
    # Existing keyhash: it reads one line and checks bcrypt.
    lines = 1 if keyhash_exists() else 2
    print(f"Creating key {name}.")
    run(
        ["secretd", "keys", "add", name, "--keyring-backend", "file"],
        password_lines=lines,
    )


def registration_stop(text: str) -> str | None:
    low = text.lower()
    if "ppid whitelist" in low or "not on the allowlist" in low:
        return "This machine is not on the allowlist."
    return None


def json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise Stop("The command did not return JSON.")
    value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise Stop("The command did not return a JSON object.")
    return value


def register(name: str, quote: Path) -> None:
    proc = run(
        [
            "secretd",
            "tx",
            "register",
            "auth",
            str(quote),
            "--from",
            name,
            "--chain-id",
            CHAIN_ID,
            "--keyring-backend",
            "file",
            "--node",
            RPC,
            "--gas",
            "700000",
            "--gas-prices",
            "0.1uscrt",
            "--yes",
            "--output",
            "json",
        ],
        password_lines=1,
        check=False,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    reason = registration_stop(combined)
    if reason:
        die(reason + " Stopped.")
    if proc.returncode != 0:
        raise Stop("tx register auth failed. Stopped.")
    body = json_object(proc.stdout or "")
    code = int(body.get("code") or 0)
    if code != 0:
        reason = registration_stop(body.get("raw_log") or "")
        die((reason or f"tx register auth failed with code {code}.") + " Stopped.")
    txhash = str(body.get("txhash") or "")
    if not re.fullmatch(r"[0-9A-Fa-f]{64}", txhash):
        raise Stop("tx register auth did not return a transaction hash. Stopped.")
    wait_for_tx(txhash)


def wait_for_tx(txhash: str) -> None:
    deadline = time.time() + 180
    while True:
        proc = run(
            ["secretd", "query", "tx", txhash, "--node", RPC, "--output", "json"],
            suppress_stdout=True,
            check=False,
        )
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode == 0 and "{" in (proc.stdout or ""):
            body = json_object(proc.stdout)
            reason = registration_stop(str(body.get("raw_log") or ""))
            if reason:
                die(reason + " Stopped.")
            code = int(body.get("code") or 0)
            if code != 0:
                die(f"tx register auth failed in a block with code {code}. Stopped.")
            print(f"Register transaction {txhash} is in a block.")
            return
        if time.time() >= deadline:
            raise Stop("The register transaction was not in a block yet. Stopped.")
        time.sleep(3)


def fetch_seed(pubkey: Path) -> None:
    run(
        ["secretd", "query", "register", "secret-network-params", "--node", RPC],
        cwd=HOME,
        suppress_stdout=True,
    )
    master = HOME / "node-master-key.txt"
    io_master = HOME / "io-master-key.txt"
    if not master.is_file() or master.stat().st_size == 0:
        raise Stop("secret-network-params did not write node-master-key.txt.")
    if not io_master.is_file() or io_master.stat().st_size == 0:
        raise Stop("secret-network-params did not write io-master-key.txt.")
    dumped = run(["secretd", "dump", str(pubkey)], suppress_stdout=True)
    node_id = "".join(dumped.stdout.split())
    if not re.fullmatch(r"[0-9a-fA-F]{64}", node_id):
        raise Stop("secretd dump did not print a 64-character node id.")
    seed_proc = run(
        ["secretd", "query", "register", "seed", node_id, "--node", RPC],
        suppress_stdout=True,
    )
    seed = seed_proc.stdout.strip()
    if seed.startswith("0x") or seed.startswith("0X"):
        seed = seed[2:]
    if not seed or len(seed) % 96 != 0 or not re.fullmatch(r"[0-9a-fA-F]+", seed):
        raise Stop("The seed query did not return a hex seed.")
    run(
        ["secretd", "configure-secret", "node-master-key.txt", seed],
        cwd=HOME,
        suppress_stdout=True,
    )
    seed_file = HOME / ".node" / "new_seed.json"
    if not seed_file.is_file() or seed_file.stat().st_size == 0:
        raise Stop("configure-secret did not write ~/.secretd/.node/new_seed.json.")


def set_toml(path: Path, section: str, key: str, literal: str) -> None:
    text = path.read_text()
    newline = "\n"
    lines = text.splitlines()
    current = ""
    replaced = False
    section_header = None
    insert_at = None
    key_re = re.compile(rf"^(\s*){re.escape(key)}\s*=")
    section_re = re.compile(r"^\s*\[([^\]]+)\]\s*(?:#.*)?$")
    for index, line in enumerate(lines):
        header = section_re.match(line)
        if header:
            if current == section and section_header is not None and insert_at is None:
                insert_at = index
            current = header.group(1).strip()
            if current == section:
                section_header = index
            continue
        if current == section and key_re.match(line):
            indent = key_re.match(line).group(1)
            lines[index] = f"{indent}{key} = {literal}"
            replaced = True
            break
    if not replaced:
        if section == "":
            at = 0
            for index, line in enumerate(lines):
                if section_re.match(line):
                    at = index
                    break
            else:
                at = len(lines)
            lines.insert(at, f"{key} = {literal}")
        else:
            if section_header is None:
                raise Stop(f"{path} has no [{section}] section.")
            at = insert_at if insert_at is not None else len(lines)
            lines.insert(at, f"{key} = {literal}")
    path.write_text(newline.join(lines) + newline)


def secret4_p2p_seeds() -> str:
    here = Path(__file__).resolve().parent
    doc = here.parent / "src/content/docs/operators/home.mdx"
    if doc.is_file():
        match = re.search(r'^seeds = "([^"]+)"', doc.read_text(), re.MULTILINE)
        if match:
            return match.group(1)
    # Same p2p.seeds line as Create the node home when the docs tree is not on disk.
    return (
        "d047c7c0431e13ef914a928f4d738870c3de932d@162.251.234.169:26656,"
        "9c530e33a6737efb14c5dc4c087188815375ed5f@162.251.234.143:26656,"
        "08a1f831254bf6198a6535011ffccbefbbcf240b@162.251.234.170:26656,"
        "d3827d7a908ffc87b62a72ee2706e3d4082ababe@162.251.234.171:26656,"
        "7fb7e3751a3aff1d70c03fa1aa19b78cb12525a5@162.251.234.172:26656,"
        "3f5ade9acf08c1dd93451e27729926645d6722e2@162.251.234.131:26656,"
        "ad039e1610dbfd507b4e91003b7c8ff1b6670e92@162.251.234.132:26656"
    )


def configure_p2p_seeds(clear_persistent_peers: bool) -> None:
    config = HOME / "config" / "config.toml"
    if not config.is_file():
        raise Stop("config.toml is missing.")
    seeds = secret4_p2p_seeds()
    set_toml(config, "p2p", "seeds", f'"{seeds}"')
    if clear_persistent_peers:
        set_toml(config, "p2p", "persistent_peers", '""')


def configure_ports(public_rpc: bool, public_grpc: bool, public_lcd: bool, prune: str) -> None:
    config = HOME / "config" / "config.toml"
    app = HOME / "config" / "app.toml"
    if not config.is_file() or not app.is_file():
        raise Stop("config.toml or app.toml is missing.")
    rpc = "tcp://127.0.0.1:26657"
    lcd = "tcp://127.0.0.1:1317"
    grpc = "127.0.0.1:9090"
    set_toml(config, "rpc", "laddr", f'"{rpc}"')
    set_toml(app, "", "pruning", f'"{prune}"')
    set_toml(app, "", "minimum-gas-prices", '"0.1uscrt"')
    set_toml(app, "", "iavl-disable-fastnode", "true")
    set_toml(app, "api", "address", f'"{lcd}"')
    set_toml(app, "grpc", "address", f'"{grpc}"')
    if public_rpc or public_grpc or public_lcd:
        set_toml(app, "api", "enabled-unsafe-cors", "false")
        print(
            "RPC, LCD, and gRPC stay on 127.0.0.1. "
            "Publish a proxy after the node is caught up. "
            "Firewall 26657, 1317, 9090, 6060, and 26660."
        )


def fetch_restore_script(dest: Path) -> None:
    bundled = Path(__file__).resolve().parent / "restore.sh"
    if bundled.is_file():
        shutil.copyfile(bundled, dest)
        return
    raise Stop(
        "restore.sh is missing next to secret-setup.py. "
        "Download it from the same host as this script, then run again."
    )


def restore_snapshot() -> None:
    dest = HOME / "restore.sh"
    fetch_restore_script(dest)
    run(["bash", str(dest)])


def main() -> None:
    global PASSWORD
    version_id, resume = check_host()
    if resume:
        print(
            "~/.secretd is already initialized; continuing from registration.",
            file=sys.stderr,
        )
        key_name = prompt("Key name: ")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", key_name):
            die("Use a key name of letters, digits, '.', '_', or '-'.")
        PASSWORD = prompt_password()
        public_rpc = prompt_yes_no("Public RPC? [yes/no]: ")
        public_grpc = prompt_yes_no("Public gRPC? [yes/no]: ")
        public_lcd = prompt_yes_no("Public LCD? [yes/no]: ")
        prune = existing_pruning() or prompt_prune()
    else:
        moniker = prompt("Moniker: ")
        if any(ord(ch) < 32 for ch in moniker):
            die("The moniker is one line.")
        key_name = prompt("Key name: ")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", key_name):
            die("Use a key name of letters, digits, '.', '_', or '-'.")
        PASSWORD = prompt_password()
        public_rpc = prompt_yes_no("Public RPC? [yes/no]: ")
        public_grpc = prompt_yes_no("Public gRPC? [yes/no]: ")
        public_lcd = prompt_yes_no("Public LCD? [yes/no]: ")
        prune = prompt_prune()

    restored = False
    try:
        install_packages()
        write_client_config()
        codename = ubuntu_codename(version_id)
        if not codename:
            die("Could not determine the Ubuntu codename for the Intel SGX apt repo.")
        azure_sgx = azure_dcsv3_vm()
        install_intel_sgx_repo(codename)
        install_deb(version_id)
        run(["secretd", "config", "set", "client", "keyring-backend", "file"])
        run(["secretd", "config", "set", "client", "chain-id", CHAIN_ID])
        if not resume:
            run(["secretd", "init", moniker, "--chain-id", CHAIN_ID])
            configure_p2p_seeds(True)
        else:
            configure_p2p_seeds(False)
        ensure_key(key_name)
        if has_seed():
            print("Seed file already present; skipping registration.", file=sys.stderr)
            configure_ports(public_rpc, public_grpc, public_lcd, prune)
            restored = run_restore_if_needed()
            if restored:
                print("Snapshot restore finished.")
            return
        ensure_funds(key_name)
        setup_sgx_runtime(version_id)
        run_init_enclave()
        fix_opt_secret_permissions()
        sgx = Path(os.environ.get("SCRT_SGX_STORAGE", "/opt/secret/.sgx_secrets"))
        quote = sgx / "attestation_combined.bin"
        pubkey = sgx / "pubkey.bin"
        if not quote.is_file() or quote.stat().st_size == 0:
            raise Stop("init-enclave did not write attestation_combined.bin.")
        register(key_name, quote)
        fetch_seed(pubkey)
        configure_ports(public_rpc, public_grpc, public_lcd, prune)
        restored = run_restore_if_needed()
    except Stop as exc:
        die(exc.message)
    if restored:
        print("Snapshot restore finished.")


if __name__ == "__main__":
    main()
