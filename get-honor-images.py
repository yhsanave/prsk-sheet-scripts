import os
import xml.etree.ElementTree as ET
from pathlib import Path
from time import sleep
from typing import List

import requests
from rich.progress import track

import config

def get_dirs(baseUrl: str, prefix: str, token: str = None) -> List[str]:
    '''Enumerates the given directory.'''

    res = requests.get(
        url=baseUrl,
        params={
            "continuation-token": token,
            "delimiter": "/",
            "list-type": "2",
            "prefix": prefix,
        })

    if not res.ok:
        print(res)
        return []

    root = ET.fromstring(res.text)
    namespace = f'{root.tag.split('}')[0]}}}'
    token = root.findtext(f"{namespace}NextContinuationToken")

    items = []
    # Get directories
    for item in root.findall(f"{namespace}CommonPrefixes/{namespace}Prefix"):
        items.append(item.text)

    # Get files
    for item in root.findall(f"{namespace}Contents/{namespace}Key"):
        items.append(item.text)

    if root.findtext(f"{namespace}IsTruncated") == "true":
        items.extend(get_dirs(baseUrl, prefix, token))

    return items


def get_paths(baseUrl: str, prefix: str, dirCachePath: str, pathCachePath: str) -> List[str]:
    '''Get all the paths to files in a given directory that aren't already in ./assets. Only goes one subdirectory deep currently.'''

    if os.path.exists(os.path.join('output', dirCachePath)):
        with open(os.path.join('output', dirCachePath), 'r') as f:
            cachedDirs = [d.strip('\n') for d in f.readlines()]
    else:
        cachedDirs = []

    dirs = get_dirs(baseUrl, prefix)

    with open(os.path.join('output', dirCachePath), 'w') as f:
        f.writelines(f'{d}\n' for d in dirs)

    newDirs = [d for d in dirs if d not in cachedDirs]

    paths: List[str] = []

    for dir in track(newDirs, "Getting paths...", transient=True):
        paths.extend(get_dirs(baseUrl, dir))
        sleep(.005)

    with open(os.path.join('output', pathCachePath), 'a') as f:
        f.writelines(f'{p}\n' for p in paths)

    with open(os.path.join('output', pathCachePath), 'r') as f:
        paths = [d.strip('\n') for d in f.readlines()]

    newPaths = [p for p in paths if not os.path.exists(
        os.path.join(config.ASSETS_DIRECTORY, *p.split('/')))]

    return newPaths


def save_image(url: str, path: str) -> bool:
    '''Download and write image file.'''
    
    response = requests.get(url, stream=True)
    if not response.ok:
        print(url, response)
        return False

    Path(*path.split(os.sep)[:-1]).mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as handle:
        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)

        return True


def get_images(paths: List[str], tryEN: bool = True):
    '''Download a list of images.'''
    for path in track(paths, "Downloading images...", transient=True):
        if not tryEN or not save_image(f'https://storage.sekai.best/sekai-en-assets/{path}', os.path.join(config.ASSETS_DIRECTORY, *path.split('/'))):
            save_image(
                f'https://storage.sekai.best/sekai-jp-assets/{path}', os.path.join(config.ASSETS_DIRECTORY, *path.split('/')))
        sleep(.05)


if __name__ == "__main__":
    # Get honors
    paths = get_paths('https://storage.sekai.best/sekai-jp-assets/',
                      'honor/', 'honorDirsCache.txt', 'honorPathsCache.txt')
    print(f'Found {len(paths)} honors to download...')
    get_images(paths)

    # Get honor_frames
    paths = get_paths('https://storage.sekai.best/sekai-jp-assets/',
                      'honor_frame/', 'honorFrameDirsCache.txt', 'honorFramePathsCache.txt')
    print(f'Found {len(paths)} honor frames to download...')
    get_images(paths, False)

    # Get rank_live honors
    paths = get_paths('https://storage.sekai.best/sekai-jp-assets/',
                      'rank_live/honor/', 'rankedHonorDirsCache.txt', 'rankedHonorPathsCache.txt')
    print(f'Found {len(paths)} ranked honors to download...')
    get_images(paths, False)
