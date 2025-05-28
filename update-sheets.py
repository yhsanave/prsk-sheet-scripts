from typing import List
import gspread
import config
from model import Card, Music
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from data import update_data

# Update Data
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