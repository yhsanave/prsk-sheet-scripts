import csv
import os

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import config
from model import Card, Music

engine = create_engine(config.DATABASE_STRING)
Session = sessionmaker(bind=engine)
session = Session()

# Cards
with open(os.path.join("output", "cards.csv"), 'w', encoding='utf8', newline='') as f:
    cards = [c.asdict() for c in session.execute(select(Card).order_by(Card.id)).scalars().all()]

    writer = csv.DictWriter(f, fieldnames=cards[0].keys())
    writer.writeheader()
    writer.writerows(cards)

# Musics
with open(os.path.join("output", "musics.csv"), 'w', encoding='utf8', newline='') as f:
    musics = [m.asdict() for m in session.execute(select(Music).order_by(Music.id)).scalars().all()]

    writer = csv.DictWriter(f, fieldnames=musics[0].keys())
    writer.writeheader()
    writer.writerows(musics)
