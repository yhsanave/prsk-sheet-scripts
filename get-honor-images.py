import os
import xml.etree.ElementTree as ET
from pathlib import Path
from time import sleep
from typing import List, Tuple

import requests
import sqlalchemy.orm
from rich.progress import (BarColumn, MofNCompleteColumn, Progress, TaskID,
                           TextColumn, TimeElapsedColumn, TimeRemainingColumn)
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import config
from model import HonorDirectory, HonorDirectoryType, HonorFile


def get_dirs(baseUrl: str, prefix: str, cachedDirs: List[str] = [], token: str = None, prog: Progress = None, progTask: TaskID = None, isContinue: bool = False) -> Tuple[List[str], List[str]]:
    '''Enumerates the given directory.'''
    if prefix in cachedDirs:
        if prog:
            prog.advance(progTask)

        return [], []

    if prog:
        prog.update(progTask, path=prefix)

    res = requests.get(
        url=baseUrl,
        params={
            "continuation-token": token,
            "delimiter": "/",
            "list-type": "2",
            "prefix": prefix,
        })
    sleep(.005)

    if not res.ok:
        print(res)
        return [], []

    root = ET.fromstring(res.text)
    namespace = f'{root.tag.split("}")[0]}}}'
    token = root.findtext(f"{namespace}NextContinuationToken")

    # Get directories
    dirs = []
    for item in root.findall(f"{namespace}CommonPrefixes/{namespace}Prefix"):
        if item.text not in cachedDirs:
            dirs.append(item.text)

    if prog:
        prog.update(progTask, total=prog.tasks[0].total + len(dirs))

    # Get files
    files = []
    for item in root.findall(f"{namespace}Contents/{namespace}Key"):
        files.append(item.text)

    # Get remaining if truncated
    if root.findtext(f"{namespace}IsTruncated") == "true":
        next = get_dirs(baseUrl, prefix, cachedDirs=cachedDirs,
                        token=token, prog=prog, progTask=progTask, isContinue=True)
        dirs.extend(next[0])
        files.extend(next[1])

    if isContinue:
        return dirs, files

    # Expand subdirectories
    hasDirs = len(dirs) > 0
    while hasDirs:
        subdirs = []
        subfiles = []
        expanded = []

        for dir in dirs:
            sub = get_dirs(baseUrl, dir, cachedDirs=cachedDirs,
                           prog=prog, progTask=progTask)
            subdirs.extend(sub[0])
            subfiles.extend(sub[1])

            if len(subdirs) > 0:
                expanded.append(dir)

        for dir in expanded:
            dirs.remove(dir)

        dirs.extend(subdirs)
        files.extend(subfiles)
        hasDirs = len(subdirs) > 0

    if prog:
        prog.advance(progTask)

    return dirs, files


def save_image(url: str, path: str) -> bool:
    '''Download and write image file.'''

    response = requests.get(url, stream=True)
    sleep(.1)
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


def get_honors(session: sqlalchemy.orm.Session, prefix: str, honorType: HonorDirectoryType):
    """Gets new honor directories and caches them in the DB"""

    cachedDirs = session.execute(select(HonorDirectory.directory).where(
        HonorDirectory.availableEN == True)).scalars().all()
    with Progress(
            TextColumn('{task.description}'),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn('{task.fields[path]}'),
            transient=True
    ) as prog:
        task = prog.add_task('Getting EN Directories', total=0, path='')
        enHonorDirs, enHonorFiles = get_dirs(
            'https://storage.sekai.best/sekai-en-assets/', prefix, cachedDirs, prog=prog, progTask=task)

    honorDirs = []
    for dir in enHonorDirs:
        session.merge(HonorDirectory(
            directory=dir,
            availableEN=True,
            dirType=honorType.value
        ))
    session.commit()

    cachedDirs = session.execute(
        select(HonorDirectory.directory)).scalars().all()
    with Progress(
        TextColumn('{task.description}'),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn('{task.fields[path]}'),
        transient=True
    ) as prog:
        task = prog.add_task('Getting JP Directories', total=0, path='')
        jpHonorDirs, jpHonorFiles = get_dirs(
            'https://storage.sekai.best/sekai-jp-assets/', prefix, cachedDirs, prog=prog, progTask=task)

    honorDirs = []
    for dir in filter(lambda d: d not in enHonorDirs, jpHonorDirs):
        honorDirs.append(HonorDirectory(
            directory=dir,
            availableEN=False,
            dirType=honorType.value
        ))
    session.add_all(honorDirs)
    session.commit()

    # Get Files
    honorFiles = []
    for file in enHonorFiles:
        honorFiles.append(HonorFile(
            filename=file.split('/')[-1],
            directoryId=file[:file.rfind('/')+1],
            downloadedEN=False
        ))
    for file in filter(lambda d: d not in enHonorFiles, jpHonorFiles):
        honorFiles.append(HonorFile(
            filename=file.split('/')[-1],
            directoryId=file[:file.rfind('/')+1],
            downloadedEN=False
        ))
    session.add_all(honorFiles)
    session.commit()


if __name__ == "__main__":
    # DB Setup
    engine = create_engine(config.DATABASE_STRING)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get Directories
    get_honors(session, 'honor/', HonorDirectoryType.HONOR)
    get_honors(session, 'honor_frame/', HonorDirectoryType.HONOR_FRAME)
    get_honors(session, 'rank_live/honor/', HonorDirectoryType.RANK_LIVE)

    # Download images
    with Progress(
        TextColumn('{task.description}'),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn('{task.fields[path]}'),
        transient=True
    ) as prog:
        newENFiles = [f for f in session.execute(
            select(
                HonorFile
            ).join(
                HonorDirectory
            ).where(
                HonorDirectory.availableEN == True
            )
        ).scalars().all() if not f.downloadedEN or not os.path.exists(f.get_path())]

        task = prog.add_task(
            'Downloading EN images',
            total=len(newENFiles),
            path=''
        )
        for f in newENFiles:
            prog.update(task, path=f.get_path())
            if save_image(f.get_url(), f.get_path()):
                f.downloadedEN = True
                session.commit()
            prog.advance(task)

        newJPFiles = [f for f in session.execute(
            select(
                HonorFile
            ).join(
                HonorDirectory
            ).where(
                HonorFile.directory
            )
        ).scalars().all() if not os.path.exists(f.get_path())]

        task = prog.add_task(
            'Downloading JP images',
            total=len(newJPFiles),
            path=''
        )
        for f in newJPFiles:
            prog.update(task, path=f.get_path())
            save_image(f.get_url(), f.get_path())
            prog.advance(task)
