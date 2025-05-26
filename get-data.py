from datetime import datetime
from typing import Dict, List
from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config
import os
import json
from model import Base, Card, GameCharacter, Music, MusicArtist, MusicDifficulty, Skill, Unit


# Fetch data repository
if not os.path.exists(config.DATA_DIRECTORY):
    print(
        f"Repository not found. Cloning repository {config.DATA_REPOSITORY_URL}...")
    repo = Repo.clone_from(config.DATA_REPOSITORY_URL, config.DATA_DIRECTORY)
else:
    print(
        f"Repository found at {config.DATA_DIRECTORY}. Pulling latest changes...")
    repo = Repo(config.DATA_DIRECTORY).remotes.origin.pull()

# Import data into database
engine = create_engine(config.DATABASE_STRING)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Import Units
with open(os.path.join(config.DATA_DIRECTORY, 'unitProfiles.json'), 'r', encoding="utf8") as f:
    unitData: List[Dict] = json.load(f)
    units = map(lambda u: Unit(
        unit=u["unit"],
        seq=u["seq"],
        unitName=u["unitName"]
    ), unitData)
    session.add_all(units)

# Import Characters
with open(os.path.join(config.DATA_DIRECTORY, 'gameCharacters.json'), 'r', encoding="utf8") as f:
    characterData: List[Dict] = json.load(f)
    characters = map(lambda c: GameCharacter(
        id=c["id"],
        firstName=c.get("firstName", None),
        givenName=c["givenName"],
        gender=c["gender"],
        unit=c["unit"]
    ), characterData)
    session.add_all(characters)

# Import Skills
with open(os.path.join(config.DATA_DIRECTORY, 'skills.json'), 'r', encoding="utf8") as f:
    skillData: List[Dict] = json.load(f)
    skills = map(lambda s: Skill(
        id=s["id"],
        skillType=Skill.parse_skill_type(s).value
    ), skillData)
    session.add_all(skills)
    
# Import Cards
with open(os.path.join(config.DATA_DIRECTORY, 'cards.json'), 'r', encoding="utf8") as f:
    cardData: List[Dict] = json.load(f)
    cards = map(lambda c: Card(
        id=c["id"],
        seq=c["seq"],
        character=c["characterId"],
        prefix=c["prefix"],
        cardRarityType=c["cardRarityType"],
        attribute=c["attr"],
        supportUnit= c["supportUnit"] if c["supportUnit"] != "none" else None,
        skill=c["skillId"],
        releaseAt=datetime.fromtimestamp(c["releaseAt"]/1000).date(),
        assetBundleName=c["assetbundleName"]
    ), cardData)
    session.add_all(cards)

# Import Music Artists
with open(os.path.join(config.DATA_DIRECTORY, 'musicArtists.json'), 'r', encoding="utf8") as f:
    artistData: List[Dict] = json.load(f)
    artists = map(lambda a: MusicArtist(
        id=a["id"],
        name=a["name"]
    ), artistData)
    session.add_all(artists)
    
# Import Music
with open(os.path.join(config.DATA_DIRECTORY, 'musics.json'), 'r', encoding="utf8") as f:
    musicData: List[Dict] = json.load(f)
    music = map(lambda m: Music(
        id=m["id"],
        seq=m["seq"],
        title=m["title"],
        creatorArtist=m.get("creatorArtistId", None),
        lyricist=m["lyricist"],
        composer=m["composer"],
        arranger=m["arranger"],
        assetBundleName=m["assetbundleName"],
        releasedAt=datetime.fromtimestamp(m.get("releasedAt", 0)/1000).date(),
        publishedAt=datetime.fromtimestamp(m["publishedAt"]/1000).date(),
        fillerSec=m["fillerSec"]
    ), musicData)
    session.add_all(music)
    
# Import Music Difficulty
with open(os.path.join(config.DATA_DIRECTORY, 'musicDifficulties.json'), 'r', encoding="utf8") as f:
    difficultyData: List[Dict] = json.load(f)
    difficulties = map(lambda d: MusicDifficulty(
        id=d["id"],
        music=d["musicId"],
        difficulty=d["musicDifficulty"],
        playLevel=d["playLevel"],
        totalNoteCount=d["totalNoteCount"]
    ), difficultyData)
    session.add_all(difficulties)

session.commit()
session.close()
