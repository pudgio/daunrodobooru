import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from colorama import init, Fore, Style
import concurrent.futures

# search arguments
def get_user_input():
    search_phrase = input('Search Phrase (like_th1s): ').strip()
    while not search_phrase:
        search_phrase = input('You have to tell me what you want to find!').strip()
    try:
        num_images = int(input('How many images should I download? (1000 max per search): '))
        if num_images < 1:
            raise ValueError
        if num_images > 1000:
            print('Too many, adjusted to 1000')
            num_images = 1000
    except ValueError:
        print('Not sure? 1 for now.')
        num_images = 1
    return search_phrase, num_images

def make_folder(search_phrase):
    today = datetime.now().strftime('%m-%d-%Y')
    safe_phrase = search_phrase.replace(' ', '_')
    folder_name = '%s_%s' % (today, safe_phrase)
    folder_path = os.path.join('images', folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path

def fetch_image_urls(search_phrase, num_images):
    urls = []
    base_url = 'https://safebooru.org/index.php?page=dapi&s=post&q=index&limit=%d&tags=%s' % (num_images, urllib.request.quote(search_phrase))
    response = urllib.request.urlopen(base_url)
    xml_data = response.read()
    root = ET.fromstring(xml_data)
    for post in root.findall('post'):
        file_url = post.get('file_url')
        if file_url:
            if file_url.startswith('http'):
                full_url = file_url
            elif file_url.startswith('//'):
                full_url = 'https:' + file_url
            elif file_url.startswith('/'):
                full_url = 'https://safebooru.org' + file_url
            else:
                full_url = 'https://safebooru.org/images/' + file_url
            urls.append(full_url)
    return urls

def download_images(urls, folder_path):
    def download_image(url, idx):
        try:
            image_name = url.split('/')[-1]
            file_name = os.path.join(folder_path, image_name)
            print(Fore.CYAN + '[%d] %s' % (idx + 1, image_name) + Style.RESET_ALL)
            urllib.request.urlretrieve(url, file_name)
        except Exception as e:
            print('Failed to download %s: %s' % (url, e))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download_image, url, idx) for idx, url in enumerate(urls)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

def main():
    if not os.path.exists('images'):
        os.makedirs('images')

    init()
    print(Style.BRIGHT + Fore.CYAN + r"""
d8888b.  .d8b.  db    db d8b   db d8888b.  .d88b.  d8888b.  .d88b.  d8888b.  .d88b.   .d88b.  d8888b. db    db 
88  `8D d8' `8b 88    88 888o  88 88  `8D .8P  Y8. 88  `8D .8P  Y8. 88  `8D .8P  Y8. .8P  Y8. 88  `8D 88    88 
88   88 88ooo88 88    88 88V8o 88 88oobY' 88    88 88   88 88    88 88oooY' 88    88 88    88 88oobY' 88    88 
88   88 88~~~88 88    88 88 V8o88 88`8b   88    88 88   88 88    88 88~~~b. 88    88 88    88 88`8b   88    88 
88  .8D 88   88 88b  d88 88  V888 88 `88. `8b  d8' 88  .8D `8b  d8' 88   8D `8b  d8' `8b  d8' 88 `88. 88b  d88 
Y8888D' YP   YP ~Y8888P' VP   V8P 88   YD  `Y88P'  Y8888D'  `Y88P'  Y8888P'  `Y88P'   `Y88P'  88   YD ~Y8888P' 
                                                                                                               
                                                                                                               
""" + Style.RESET_ALL)
    print(Fore.LIGHTRED_EX + "**if your search has no results, it's likely they're nsfw and won't be downloaded because of safebooru's tos**" + Style.RESET_ALL)
    while True:
        search_phrase, num_images = get_user_input()
        folder_path = make_folder(search_phrase)
        urls = fetch_image_urls(search_phrase, num_images)
        if not urls:
            print('No images found for "%s".' % search_phrase)
            # delete junk folder
            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
                print('Empty folder deleted:', folder_path)
        else:
            download_images(urls, folder_path)
            # verify download completion
            if os.path.exists(folder_path) and not os.listdir(folder_path):
                os.rmdir(folder_path)
                print('I couldn\'t find anything, folder deleted.', folder_path)
            else:
                print('Fetched %d images to %s' % (len(os.listdir(folder_path)), folder_path))
        again = input('Wanna search again? [Y/N]: ').strip().lower()
        if again != 'y':
            break

if __name__ == '__main__':
    main()
