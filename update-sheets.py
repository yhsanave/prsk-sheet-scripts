import argparse
import glob
import os
from itertools import groupby
from typing import List

import gspread
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import config
from data import update_data
from model import Card, Music

GITHUB_BASE_URL = r'https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/refs/heads/main'
CR_TITLES_PATH = os.path.join(
    config.ASSETS_DIRECTORY, 'honor_baked', 'character')
ACHIEVEMENT_TITLES_PATH = os.path.join(
    config.ASSETS_DIRECTORY, 'honor_baked', 'achievement')

parser = argparse.ArgumentParser(
    prog='update-sheets',
    description='Updates the master spreadsheet with the latest data.'
)
parser.add_argument('-nu', '--no-update', action='store_true',
                    help='Skip updating the DB. Use this if you have already pulled the DB.')
args = vars(parser.parse_args())

# Get latest data
if not args.get('no_update'):
    update_data()

# Database Setup
engine = create_engine(config.DATABASE_STRING)
Session = sessionmaker(bind=engine)
session = Session()

# Google Sheets Setup
gc = gspread.service_account(filename=config.GOOGLE_API_KEY_PATH)
masterSpread = gc.open_by_key(config.MASTER_SHEET_ID)

# Get Cards
cards = session.execute(select(Card).order_by(Card.id)).scalars().all()
cardRows: List[List] = [c.to_row() for c in cards]
cardHeaders = cards[0].get_row_headers()

# Get Musics
musics = session.execute(select(Music).order_by(Music.id)).scalars().all()
musicRows: List[List] = [m.to_row() for m in musics]
musicHeaders = musics[0].get_row_headers()

# Write Sheets
print('Writing Cards sheet...')
cardSheet = masterSpread.worksheet('Cards')
cardSheet.clear()
cardSheet.update([cardHeaders], 'A1')
cardSheet.update(cardRows, 'A2')

print('Writing Musics sheet...')
musicSheet = masterSpread.worksheet('Musics')
musicSheet.clear()
musicSheet.update([musicHeaders], 'A1')
musicSheet.update(musicRows, 'A2')

# CR Titles
print("Writing CR Titles sheet...")
crTitleSheet = masterSpread.worksheet("CR Titles")
crTitleSheet.clear()
crTitleSheet.update([['Main', *range(0, 165, 5)]], 'A1')

crDegrees = glob.glob('**/main/*.png', root_dir=CR_TITLES_PATH, recursive=True)
rows = []
for k, g in groupby(crDegrees, lambda p: p.split(os.path.sep)[0]):
    rows.append([
        k[3:].replace('-', ' '),
        *[f'{GITHUB_BASE_URL}/honor_baked/character/{p.replace(os.path.sep, "/")}' for p in g]
    ])
crTitleSheet.update(rows, 'A2', value_input_option='USER_ENTERED')

crTitleSheet.update([['Sub', *range(0, 165, 5)]], 'A28')
crDegrees = glob.glob('**/sub/*.png', root_dir=CR_TITLES_PATH, recursive=True)
rows = []
for k, g in groupby(crDegrees, lambda p: p.split(os.path.sep)[0]):
    rows.append([
        k[3:].replace('-', ' '),
        *[f'{GITHUB_BASE_URL}/honor_baked/character/{p.replace(os.path.sep, "/")}' for p in g]
    ])
crTitleSheet.update(rows, 'A29', value_input_option='USER_ENTERED')

# Achievement Titles
print("Writing Achievement sheets...")
achievementSheetMain = masterSpread.worksheet("Achievements Main")
achievementDegreesMain = glob.glob(
    '**/main/*.png', root_dir=ACHIEVEMENT_TITLES_PATH, recursive=True)
rows = []
for k, g in groupby(achievementDegreesMain, lambda p: p.split(os.path.sep)[0]):
    rows.append([
        k[5:].replace('-', ' '),
        *[f'{GITHUB_BASE_URL}/honor_baked/achievement/{p.replace(os.path.sep, "/")}' for p in g]
    ])
achievementSheetMain.clear()
achievementSheetMain.update(rows, 'A1', value_input_option='USER_ENTERED')

achievementSheetSub = masterSpread.worksheet("Achievements Sub")
achievementDegreesSub = glob.glob(
    '**/sub/*.png', root_dir=ACHIEVEMENT_TITLES_PATH, recursive=True)
rows = []
for k, g in groupby(achievementDegreesSub, lambda p: p.split(os.path.sep)[0]):
    rows.append([
        k[5:].replace('-', ' '),
        *[f'{GITHUB_BASE_URL}/honor_baked/achievement/{p.replace(os.path.sep, "/")}' for p in g]
    ])
achievementSheetSub.clear()
achievementSheetSub.update(rows, 'A1', value_input_option='USER_ENTERED')
