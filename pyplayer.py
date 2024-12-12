import subprocess
import sys
from pytube import Search
import yt_dlp
import time
from tqdm import tqdm
import re
from colorama import Fore, Style, init

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

def search_youtube(query, max_results=50):
    """Search YouTube using pytube and return top max_results results."""
    try:
        search = Search(query)
        print(f"{Fore.YELLOW}Searching YouTube... Please wait.")
        time.sleep(2)  # Simulate delay for loading results (for demo purposes)
        search_results = search.results[:max_results]  # Limit the number of results
        return [(video.title, video.watch_url) for video in search_results]
    except Exception as e:
        print(f"{Fore.RED}Error while searching: {e}")
        return []

def is_valid_url(url):
    """Check if the input is a valid YouTube URL."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.*v=([a-zA-Z0-9_-]{11})'
    )
    return re.match(youtube_regex, url)

def choose_video(videos):
    """Use fzf to choose a video interactively."""
    video_titles = [f"{video[0]} | {video[1]}" for video in videos]
    
    # Use fzf for interactive fuzzy search
    print(f"{Fore.YELLOW}Choosing video... Use fzf to select.")
    chosen_video = subprocess.run(
        ["fzf"], input="\n".join(video_titles), text=True, capture_output=True
    ).stdout.strip()
    
    # Extract the video URL from the fzf output
    for title, url in videos:
        if title in chosen_video:
            return url
    return None

def download_video(url):
    """Download the video using yt-dlp."""
    global pbar  # Progress bar to be updated in the hook
    print(f"{Fore.YELLOW}Downloading video... Please wait.")
    ydl_opts = {
        'format': 'best',
        'outtmpl': '%(title)s.%(ext)s',  # Save as video title
        'progress_hooks': [yt_dlp_progress_hook]
    }
    
    # Create a tqdm progress bar with custom color and format
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
    """Progress hook to track download progress in tqdm."""
    if d['status'] == 'downloading':
        percent = d.get('downloaded_bytes', 0) * 100 // d.get('total_bytes', 1)
        pbar.n = percent
        pbar.refresh()
    elif d['status'] == 'finished':
        pbar.n = 100
        pbar.refresh()
        print(f"\n{Fore.GREEN}Download complete!")

def play_video(url):
    """Play the video using mpv."""
    print(f"{Fore.YELLOW}Playing video with mpv...")
    subprocess.run(["mpv", url])

def main():
    # Display ASCII art banner
    print(BANNER)

    # Get the search query or URL from the command-line argument or prompt user
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
    else:
        user_input = input(f"{Fore.CYAN}Enter a YouTube search query or URL: {Style.RESET_ALL}")

    # If the user input is a valid URL, we will directly download or play it
    if is_valid_url(user_input):
        selected_video_url = user_input
        print(f"{Fore.GREEN}Valid URL detected: {selected_video_url}")
    else:
        # Search for videos on YouTube if input is a name query
        print(f"{Fore.CYAN}Searching for '{user_input}' on YouTube...")
        videos = search_youtube(user_input)

        # If no videos found
        if not videos:
            print(f"{Fore.RED}No videos found.")
            return

        # Let the user choose a video using fzf
        selected_video_url = choose_video(videos)

        if not selected_video_url:
            print(f"{Fore.RED}No video selected.")
            return

    print(f"{Fore.GREEN}Selected video URL: {selected_video_url}")
    
    # Ask user whether to download or play the video
    action = input(f"{Fore.CYAN}Do you want to (d)ownload or (p)lay the video? (d/p): {Style.RESET_ALL}").strip().lower()
    
    if action == "d":
        download_video(selected_video_url)
    elif action == "p":
        print(f"{Fore.YELLOW}Loading and playing video...")
        play_video(selected_video_url)
    else:
        print(f"{Fore.RED}Invalid option. Exiting.")

if __name__ == "__main__":
    main()

