import subprocess
import sys
from pytube import Search
import yt_dlp
from tqdm import tqdm
import re
from colorama import Fore, Style, init
import os
import json

# Initialize colorama
init(autoreset=True)

# ASCII Art Banner
BANNER = f"""
{Fore.CYAN}{Style.BRIGHT}
░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓███████▓▒░  
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓███████▓▒░ ░▒▓██████▓▒░ ░▒▓█████████████▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
                                                                                       
{Style.RESET_ALL}
"""

CACHE_FILE = "video_cache.json"


def load_cache():
    """Load the cache from a JSON file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save the cache to a JSON file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=4)


def is_package_installed(package_name):
    try:
        result = subprocess.call(["which", package_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result == 0
    except Exception as e:
        print(f"Error checking if {package_name} is installed: {e}")
        return False


def detect_package_manager():
    try:
        if subprocess.call(["which", "apt"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "apt", "sudo apt update && sudo apt install -y"
        elif subprocess.call(["which", "dnf"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "dnf", "sudo dnf install -y"
        elif subprocess.call(["which", "yum"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "yum", "sudo yum install -y"
        elif subprocess.call(["which", "pacman"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "pacman", "sudo pacman -S --noconfirm"
        elif subprocess.call(["which", "zypper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "zypper", "sudo zypper install -y"
        elif subprocess.call(["which", "emerge"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return "emerge", "sudo emerge"
        else:
            return None, None
    except Exception as e:
        print(f"Error detecting package manager: {e}")
        return None, None


def install_package(package_name):
    if is_package_installed(package_name):
        print(f"{package_name} is already installed.")
    else:
        manager, command = detect_package_manager()
        if manager and command:
            print(f"Detected package manager: {manager}")
            install_command = f"{command} {package_name}"
            print(f"Installing {package_name} using: {install_command}")
            os.system(install_command)
        else:
            print("No supported package manager detected on this system.")


def search_youtube(query, max_results=50):
    try:
        search = Search(query)
        print(f"{Fore.YELLOW}Searching YouTube... Please wait.")
        search_results = search.results[:max_results]
        return [(video.title, video.watch_url) for video in search_results]
    except Exception as e:
        print(f"{Fore.RED}Error while searching: {e}")
        return []


def is_valid_url(url):
    youtube_regex = (
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})(?:\?[^\s]*)?'
    )
    return bool(re.fullmatch(youtube_regex, url))


def choose_video(videos):
    video_titles = [f"{video[0]} | {video[1]}" for video in videos]
    print(f"{Fore.YELLOW}Choosing video... Use fzf to select.")
    chosen_video = subprocess.run(
        ["fzf"], input="\n".join(video_titles), text=True, capture_output=True
    ).stdout.strip()
    for title, url in videos:
        if title in chosen_video:
            return url
    return None


def download_video(url, resolution="best"):
    global pbar
    print(f"{Fore.YELLOW}Downloading video... Please wait.")
    ydl_opts = {
        'format': f'bestvideo[height<={resolution}]+bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [yt_dlp_progress_hook]
    }
    with tqdm(
        total=100, 
        desc=f"{Fore.GREEN}Downloading", 
        bar_format="{l_bar}{bar}| {percentage:.1f}%", 
        ncols=100,
        ascii=" █▒░"
    ) as bar:
        global pbar
        pbar = bar
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])


def yt_dlp_progress_hook(d):
    if d['status'] == 'downloading':
        percent = d.get('downloaded_bytes', 0) * 100 // d.get('total_bytes', 1)
        pbar.n = percent
        pbar.refresh()
    elif d['status'] == 'finished':
        pbar.n = 100
        pbar.refresh()
        print(f"\n{Fore.GREEN}Download complete!")


def play_video(url, player):
    print(f"{Fore.YELLOW}Playing video with {player}...")
    subprocess.run([player, url])


def main():
    print(BANNER)
    cache = load_cache()

    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = input(f"{Fore.CYAN}Enter a YouTube search query or URL: {Style.RESET_ALL}")

    if is_valid_url(user_input):  # Check if it's a valid URL
        selected_video_url = user_input  # Directly assign URL
    else:
        print(f"{Fore.CYAN}Searching for '{user_input}' on YouTube...")
        videos = search_youtube(user_input)

        if not videos:
            print(f"{Fore.RED}No videos found.")
            return

        selected_video_url = choose_video(videos)

        if not selected_video_url:
            print(f"{Fore.RED}No video selected.")
            return

    if selected_video_url in cache:
        print(f"{Fore.GREEN}Video already downloaded: {cache[selected_video_url]}")
        return

    print(f"{Fore.GREEN}Selected video URL: {selected_video_url}")
    action = input(f"{Fore.CYAN}Do you want to (d)ownload or (p)lay the video? (d/p): {Style.RESET_ALL}").strip().lower()

    if action == "d":
        resolution = input(f"{Fore.CYAN}Enter resolution (e.g., 720, 1080, best): {Style.RESET_ALL}").strip() or "720"
        download_video(selected_video_url, resolution)
        cache[selected_video_url] = resolution
        save_cache(cache)
    elif action == "p":
        action_player = input(f"{Fore.CYAN}Do you want to use vlc or mpv? (v/m): {Style.RESET_ALL}").strip().lower()
        if action_player == "v":
            install_package("vlc")
            play_video(selected_video_url, "vlc")
        elif action_player == "m":
            install_package("mpv")
            play_video(selected_video_url, "mpv")
    else:
        print(f"{Fore.RED}Invalid option. Exiting.")

if __name__ == "__main__":
    main()

