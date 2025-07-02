import argparse
import glob
import os
import re
from dataclasses import dataclass
from itertools import chain, groupby
from pathlib import Path
import shutil
from typing import List

from pathvalidate import sanitize_filename
from PIL import Image
from rich.progress import track
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from git import Repo

import config
from data import update_data
from model import Honor, HonorLevel, HonorRarity, HonorType

DEGREE_MAIN_SIZE = (380, 80)
DEGREE_SUB_SIZE = (180, 80)

HONOR_LEVEL_PIP_POS = [(50, 64), (66, 64), (82, 64), (98, 64), (114, 64),
                       (50, 64), (66, 64), (82, 64), (98, 64), (114, 64)]
FC_HONOR_LEVEL_STAR_POS = [(225, 60), (217, 46), (209, 32), (217, 18), (225, 4),
                           (298, 60), (306, 46), (314, 32), (306, 18), (298, 4)]

HONOR_PATH = os.path.join(config.ASSETS_DIRECTORY, 'honor')
RANK_LIVE_PATH = os.path.join(config.ASSETS_DIRECTORY, 'rank_live', 'honor')
FRAME_PATH = os.path.join(config.ASSETS_DIRECTORY, 'frame')
HONOR_FRAME_PATH = os.path.join(config.ASSETS_DIRECTORY, 'honor_frame')

DEGREE_LV_0_PATH = os.path.join(FRAME_PATH, 'icon_degreeLv.png')
DEGREE_LV_6_PATH = os.path.join(FRAME_PATH, 'icon_degreeLv6.png')

BAKED_PATH = os.path.join(config.ASSETS_DIRECTORY, 'honor_baked')

HONOR_REQUIREMENT_PATTERN = re.compile(r'.*?([\d,]+)')
WORLD_LINK_ASSETBUNDLE_PATTERN = re.compile(r'.*(_cp\d)$')


def parse_req(description: str) -> str:
    return HONOR_REQUIREMENT_PATTERN.match(description).group(1).replace(',', '')


@dataclass
class DegreeImage:
    honor: Honor
    honorLevel: HonorLevel | None
    isSub: bool

    def __init__(self, honor: Honor, honorLevel: HonorLevel = None, isSub: bool = False):
        self.honor = honor
        self.honorLevel = honorLevel
        self.isSub = isSub

    def is_world_link(self) -> bool:
        assetbundleName = i.honorLevel.assetbundleName if i.honorLevel and i.honorLevel.assetbundleName else i.honor.assetbundleName
        return WORLD_LINK_ASSETBUNDLE_PATTERN.match(assetbundleName) is not None

    def get_bg_image(self) -> Image.Image:
        '''Returns the degree background image.'''
        if HonorType(self.honor.group.honorType) == HonorType.RANK_MATCH:
            path = os.path.join(
                RANK_LIVE_PATH, self.honor.group.backgroundAssetbundleName)
        elif self.honor.group.backgroundAssetbundleName:
            path = os.path.join(
                HONOR_PATH, self.honor.group.backgroundAssetbundleName)
        elif self.honorLevel and self.honorLevel.assetbundleName:
            path = os.path.join(HONOR_PATH, self.honorLevel.assetbundleName)
        elif self.honor.assetbundleName:
            path = os.path.join(HONOR_PATH, self.honor.assetbundleName)

        if not os.path.exists(path):
            return Image.new("RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)
        return Image.open(os.path.join(path, 'degree_sub.webp' if self.isSub else 'degree_main.webp'))

    def get_frame_image(self) -> Image.Image:
        '''Returns the degree frame image.'''
        rarity = HonorRarity(self.honorLevel.honorRarity) if self.honorLevel and self.honorLevel.honorRarity else HonorRarity(
            self.honor.honorRarity)
        rarityLv = [HonorRarity.LOW, HonorRarity.MIDDLE,
                    HonorRarity.HIGH, HonorRarity.HIGHEST].index(rarity)+1
        filename = f'frame_degree_{'s' if self.isSub else 'm'}_{rarityLv}.png'

        if rarityLv > 2 and self.honor.group.frameName:
            path = os.path.join(
                HONOR_FRAME_PATH, self.honor.group.frameName, filename)
        else:
            path = os.path.join(FRAME_PATH, filename)

        return Image.open(path)

    def get_rank_image(self) -> Image.Image | None:
        '''Returns the degree rank image.'''
        im = Image.new(
            "RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)

        if HonorType(self.honor.group.honorType) == HonorType.EVENT:
            path = os.path.join(HONOR_PATH, self.honor.assetbundleName,
                                'rank_sub.webp' if self.isSub else 'rank_main.webp')
        elif HonorType(self.honor.group.honorType) == HonorType.RANK_MATCH:
            path = os.path.join(RANK_LIVE_PATH, os.path.join(*self.honor.assetbundleName.split('/')),
                                'sub.webp' if self.isSub else 'main.webp')
        elif self.honor.honorMissionType:
            path = os.path.join(
                HONOR_PATH, self.honorLevel.assetbundleName, 'scroll.webp')
        else:
            return im

        if not os.path.exists(path):
            return im

        rankImage = Image.open(path)
        if self.is_world_link():
            pos = (0, 0)
        elif self.honor.honorMissionType:
            pos = ((im.width-rankImage.width)//2,
                   0) if self.isSub else (220, 0)
        elif self.isSub:
            pos = ((im.width-rankImage.width)//2, 40)
        else:
            pos = (200, 0)

        im.paste(rankImage, pos)
        return im

    def get_level_stars(self) -> Image.Image:
        '''Returns the degree level stars. Used for full combo achievement honors.'''
        im = Image.new(
            "RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)
        if self.isSub:
            return im

        slot = Image.open(os.path.join(
            FRAME_PATH, 'icon_degreeStar_Transparent.png')).convert("LA")
        star = Image.open(os.path.join(FRAME_PATH, 'icon_degreeStar.png'))

        for pos in FC_HONOR_LEVEL_STAR_POS:
            im.paste(slot, pos, slot)

        for pos in FC_HONOR_LEVEL_STAR_POS[:((self.honorLevel.level-1) % 10)+1]:
            im.paste(star, pos, star)

        return im

    def get_level_pips(self) -> Image.Image:
        '''Returns the degree level pips image.'''
        im = Image.new(
            "RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)

        lv0Image = Image.open(DEGREE_LV_0_PATH)
        lv6Image = Image.open(DEGREE_LV_6_PATH)

        for i in range(0, self.honorLevel.level):
            im.paste(lv0Image if i < 5 else lv6Image, HONOR_LEVEL_PIP_POS[i])

        return im

    def get_level_image(self) -> Image.Image:
        '''Returns the degree level pips image.'''
        if self.honor.honorMissionType:
            return self.get_level_stars()
        if HonorType(self.honor.group.honorType) == HonorType.CHARACTER or (HonorType(self.honor.group.honorType) == HonorType.ACHIEVEMENT and len(self.honor.levels) > 1):
            return self.get_level_pips()
        return Image.new("RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)

    def get_degree_image(self) -> Image.Image:
        '''Returns the complete degree image.'''
        layers = [
            self.get_bg_image(),
            self.get_frame_image(),
            self.get_rank_image(),
            self.get_level_image()
        ]

        im = Image.new(
            "RGBA", DEGREE_SUB_SIZE if self.isSub else DEGREE_MAIN_SIZE)

        for l in layers:
            im.paste(l, (0, 0), l)

        return im

    def get_save_path(self) -> str:
        match HonorType(self.honor.group.honorType):
            case HonorType.CHARACTER:
                charLevel = parse_req(self.honorLevel.description)
                return os.path.join(
                    BAKED_PATH,
                    i.honor.group.honorType,
                    sanitize_filename(
                        f'{i.honor.group.id:02d}-{i.honor.group.name}'),
                    'sub' if self.isSub else 'main',
                    f'CR{int(charLevel):03d}.png'
                ).replace(' ', '-')
            case HonorType.ACHIEVEMENT if len(self.honor.levels) > 1 or len(self.honor.group.honors) > 1:
                req = parse_req(self.honorLevel.description)
                levels = chain(*[h.levels for h in self.honor.group.honors])
                padding = max(len(parse_req(l.description)) for l in levels)
                return os.path.join(
                    BAKED_PATH,
                    i.honor.group.honorType,
                    sanitize_filename(
                        f'{i.honor.group.id:04d}-{i.honor.group.name}'),
                    'sub' if self.isSub else 'main',
                    '{1:0{0}}.png'.format(padding, int(req))
                ).replace(' ', '-')
            case _:
                return os.path.join(
                    BAKED_PATH,
                    i.honor.group.honorType,
                    sanitize_filename(
                        f'{i.honor.group.id:04d}-{i.honor.group.name}'),
                    'sub' if self.isSub else 'main',
                    sanitize_filename(f'{self.honor.name}.png')
                ).replace(' ', '-')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='bake-honors',
        description='Compiles the components of each honor into a single static image'
    )
    parser.add_argument('-nu', '--no-update', action='store_true', help='Skip updating the DB. Use this if you have already pulled the DB.')
    args = vars(parser.parse_args())

    # Get latest data
    if not args.get('no_update'):
        update_data()

    # DB Setup
    engine = create_engine(config.DATABASE_STRING)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Get Honors
    honors = session.execute(select(Honor)).scalars().all()

    # Generate Images
    shutil.rmtree(BAKED_PATH)

    mainImages: List[DegreeImage] = []
    subImages: List[DegreeImage] = []
    for h in track(honors, "Getting degrees...", transient=True):
        if not h.levels:
            mainImages.append(DegreeImage(h))
            subImages.append(DegreeImage(h, isSub=True))
            continue

        for l in h.levels:
            mainImages.append(DegreeImage(h, l))
            subImages.append(DegreeImage(h, l, True))

    for i in track(mainImages, "Generating main images...", transient=True):
        path = i.get_save_path()
        Path(*path.split(os.sep)[:-1]).mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            i.get_degree_image().save(f)

    for i in track(subImages, "Generating sub images...", transient=True):
        path = i.get_save_path()
        Path(*path.split(os.sep)[:-1]).mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            i.get_degree_image().save(f)

    # Generate greyed out CR0 Titles
    for i in track(glob.glob('**/CR005.png', root_dir=os.path.join(BAKED_PATH, 'character'), recursive=True), "Generating CR0 images...", transient=True):
        im = Image.open(os.path.join(BAKED_PATH, 'character', i)).convert('LA')
        im.save(os.path.join(BAKED_PATH, 'character',
                *i.split(os.sep)[:-1], 'CR000.png'))

    # Generate greyed out level 0 titles
    achievements = glob.glob(
        '**/*.png', root_dir=os.path.join(BAKED_PATH, 'achievement'), recursive=True)
    for k, g in track(groupby(achievements, lambda p: p.split(os.sep)[0:2]), "Generating LV0 images...", transient=True):
        i = next(g)
        if i.endswith(os.sep + '0000.png'):
            i = next(g)
        im = Image.open(os.path.join(
            BAKED_PATH, 'achievement', i)).convert('LA')
        im.save(os.path.join(BAKED_PATH, 'achievement',
                *i.split(os.sep)[:-1], '0000.png'))
