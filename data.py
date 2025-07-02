import json
import os
from datetime import datetime
from typing import Dict, Iterable, List

from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from model import (Base, Card, CardEpisode, CardSupply, GameCharacter, Honor,
                   HonorGroup, HonorLevel, Music, MusicArtist, MusicDifficulty,
                   MusicOriginal, MusicTag, Skill, Unit)


def merge_data(subset: Iterable, superset: Iterable) -> List:
    subset = list(subset)
    superset = list(superset)
    subIds = [x.id for x in subset]
    missing = [x for x in superset if x.id not in subIds]
    return [*subset, *missing]


def fetch_data():
    """Clone/Pull the data repositories."""
    if not os.path.exists(config.DATA_DIRECTORY_JP):
        print(
            f"JP Repository not found. Cloning repository {config.DATA_REPOSITORY_JP_URL}...")
        repo = Repo.clone_from(
            config.DATA_REPOSITORY_JP_URL, config.DATA_DIRECTORY_JP)
    else:
        print(
            f"JP Repository found at {config.DATA_DIRECTORY_JP}. Pulling latest changes...")
        repo = Repo(config.DATA_DIRECTORY_JP).remotes.origin.pull()

    if not os.path.exists(config.DATA_DIRECTORY_EN):
        print(
            f"EN Repository not found. Cloning repository {config.DATA_REPOSITORY_EN_URL}...")
        repo = Repo.clone_from(
            config.DATA_REPOSITORY_EN_URL, config.DATA_DIRECTORY_EN)
    else:
        print(
            f"EN Repository found at {config.DATA_DIRECTORY_EN}. Pulling latest changes...")
        repo = Repo(config.DATA_DIRECTORY_EN).remotes.origin.pull()


def import_data():
    """Parse the data from the repository and insert it into the database."""
    engine = create_engine(config.DATABASE_STRING)
    Base.metadata.drop_all(engine, [Base.metadata.tables[t] for t in Base.metadata.tables if t.startswith('data_')])
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Import Units
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'unitProfiles.json'), 'r', encoding="utf8") as f:
        unitData: List[Dict] = json.load(f)
        units = map(lambda u: Unit(
            unit=u["unit"],
            seq=u["seq"],
            unitName=u["unitName"]
        ), unitData)

    session.add_all(units)
    print(f"Imported {len(unitData)} units.")

    # Import Characters
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'gameCharacters.json'), 'r', encoding="utf8") as f:
        characterData: List[Dict] = json.load(f)
        characters = map(lambda c: GameCharacter(
            id=c["id"],
            firstName=c.get("firstName", None),
            givenName=c["givenName"],
            gender=c["gender"],
            unitId=c["unit"]
        ), characterData)

    session.add_all(characters)
    print(f"Imported {len(characterData)} characters.")

    # Import Skills
    with open(os.path.join(config.DATA_DIRECTORY_JP, 'skills.json'), 'r', encoding="utf8") as f:
        skillData: List[Dict] = json.load(f)
        skillsEN = map(lambda s: Skill(
            id=s["id"],
            skillType=Skill.parse_skill_type(s).value
        ), skillData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'skills.json'), 'r', encoding="utf8") as f:
        skillData: List[Dict] = json.load(f)
        skillsJP = map(lambda s: Skill(
            id=s["id"],
            skillType=Skill.parse_skill_type(s).value
        ), skillData)

    skills = merge_data(skillsEN, skillsJP)
    session.add_all(skills)
    print(f"Imported {len(skills)} skills.")

    # Import Card Supplies
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'cardSupplies.json'), 'r', encoding="utf8") as f:
        supplyData: List[Dict] = json.load(f)
        suppliesEN = map(lambda s: CardSupply(
            id=s["id"],
            cardSupplyType=s["cardSupplyType"]
        ), supplyData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'cardSupplies.json'), 'r', encoding="utf8") as f:
        supplyData: List[Dict] = json.load(f)
        suppliesJP = map(lambda s: CardSupply(
            id=s["id"],
            cardSupplyType=s["cardSupplyType"]
        ), supplyData)

    supplies = merge_data(suppliesEN, suppliesJP)
    session.add_all(supplies)
    print(f"Imported {len(supplies)} cardSupplies.")

    # Import Cards
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'cards.json'), 'r', encoding="utf8") as f:
        cardData: List[Dict] = json.load(f)
        cardsEN = map(lambda c: Card(
            id=c["id"],
            seq=c["seq"],
            characterId=c["characterId"],
            prefix=c["prefix"],
            cardRarityType=c["cardRarityType"],
            attribute=c["attr"],
            supportUnitId=c["supportUnit"] if c["supportUnit"] != "none" else None,
            skillId=c["skillId"],
            releaseAt=datetime.fromtimestamp(c["releaseAt"]/1000).date(),
            assetBundleName=c["assetbundleName"],
            cardSupplyId=c["cardSupplyId"],
            availableEN=datetime.now().timestamp() >= c["releaseAt"]/1000
        ), cardData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'cards.json'), 'r', encoding="utf8") as f:
        cardData: List[Dict] = json.load(f)
        cardsJP = map(lambda c: Card(
            id=c["id"],
            seq=c["seq"],
            characterId=c["characterId"],
            prefix=c["prefix"],
            cardRarityType=c["cardRarityType"],
            attribute=c["attr"],
            supportUnitId=c["supportUnit"] if c["supportUnit"] != "none" else None,
            skillId=c["skillId"],
            # add a year to JP release dates
            releaseAt=datetime.fromtimestamp(
                c["releaseAt"]/1000 + 31557600).date(),
            assetBundleName=c["assetbundleName"],
            cardSupplyId=c["cardSupplyId"],
            availableEN=False
        ), cardData)

    cards = merge_data(cardsEN, cardsJP)
    session.add_all(cards)
    print(f"Imported {len(cards)} cards.")

    # Import Card Episodes
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'cardEpisodes.json'), 'r', encoding="utf8") as f:
        episodeData: List[Dict] = json.load(f)
        episodesEN = map(lambda e: CardEpisode(
            id=e["id"],
            seq=e["seq"],
            cardId=e["cardId"],
        ), episodeData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'cardEpisodes.json'), 'r', encoding="utf8") as f:
        episodeData: List[Dict] = json.load(f)
        episodesJP = map(lambda e: CardEpisode(
            id=e["id"],
            seq=e["seq"],
            cardId=e["cardId"],
        ), episodeData)

    episodes = merge_data(episodesEN, episodesJP)
    session.add_all(episodes)
    print(f"Imported {len(episodes)} cardEpisodes.")

    # Import Music Artists
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'musicArtists.json'), 'r', encoding="utf8") as f:
        artistData: List[Dict] = json.load(f)
        artistsEN = map(lambda a: MusicArtist(
            id=a["id"],
            name=a["name"]
        ), artistData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'musicArtists.json'), 'r', encoding="utf8") as f:
        artistData: List[Dict] = json.load(f)
        artistsJP = map(lambda a: MusicArtist(
            id=a["id"],
            name=a["name"]
        ), artistData)

    artists = merge_data(artistsEN, artistsJP)
    session.add_all(artists)
    print(f"Imported {len(artists)} music artists.")

    # Import Music Tags
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'musicTags.json'), 'r', encoding="utf8") as f:
        tagData: List[Dict] = json.load(f)
        tagsEN = map(lambda t: MusicTag(
            id=t["id"],
            musicId=t["musicId"],
            musicTag=t["musicTag"],
            seq=t["seq"]
        ), tagData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'musicTags.json'), 'r', encoding="utf8") as f:
        tagData: List[Dict] = json.load(f)
        tagsJP = map(lambda t: MusicTag(
            id=t["id"],
            musicId=t["musicId"],
            musicTag=t["musicTag"],
            seq=t["seq"]
        ), tagData)

    musicTags = merge_data(tagsEN, tagsJP)
    session.add_all(musicTags)
    print(f"Imported {len(musicTags)} music tags.")

    # Import Music Originals
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'musicOriginals.json'), 'r', encoding="utf8") as f:
        musicOrigData: List[Dict] = json.load(f)
        musicOrigEN = map(lambda o: MusicOriginal(
            id=o["id"],
            musicId=o["musicId"],
            videoLink=o["videoLink"]
        ), musicOrigData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'musicOriginals.json'), 'r', encoding="utf8") as f:
        musicOrigData: List[Dict] = json.load(f)
        musicOrigJP = map(lambda o: MusicOriginal(
            id=o["id"],
            musicId=o["musicId"],
            videoLink=o["videoLink"]
        ), musicOrigData)

    musicOrigs = merge_data(musicOrigEN, musicOrigJP)
    session.add_all(musicOrigs)
    print(f"Imported {len(musicOrigs)} music originals.")

    # Import Music
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'musics.json'), 'r', encoding="utf8") as f:
        musicData: List[Dict] = json.load(f)
        musicEN = map(lambda m: Music(
            id=m["id"],
            seq=m["seq"],
            title=m["title"],
            creatorArtistId=m.get("creatorArtistId", None),
            lyricist=m["lyricist"],
            composer=m["composer"],
            arranger=m["arranger"],
            assetBundleName=m["assetbundleName"],
            releasedAt=datetime.fromtimestamp(
                m.get("releasedAt", 0)/1000).date(),
            publishedAt=datetime.fromtimestamp(m["publishedAt"]/1000).date(),
            fillerSec=m["fillerSec"],
            catMV="mv" in m["categories"],
            catMV2D="mv_2d" in m["categories"],
            catOriginal="original" in m["categories"],
            catImage="image" in m["categories"],
            availableEN=datetime.now().timestamp() >= m["publishedAt"]/1000
        ), musicData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'musics.json'), 'r', encoding="utf8") as f:
        musicData: List[Dict] = json.load(f)
        musicJP = map(lambda m: Music(
            id=m["id"],
            seq=m["seq"],
            title=m["title"],
            creatorArtistId=m.get("creatorArtistId", None),
            lyricist=m["lyricist"],
            composer=m["composer"],
            arranger=m["arranger"],
            assetBundleName=m["assetbundleName"],
            releasedAt=datetime.fromtimestamp(
                m.get("releasedAt", 0)/1000).date(),
            # add a year to JP release dates
            publishedAt=datetime.fromtimestamp(
                m["publishedAt"]/1000 + 31557600).date(),
            fillerSec=m["fillerSec"],
            catMV="mv" in m["categories"],
            catMV2D="mv_2d" in m["categories"],
            catOriginal="original" in m["categories"],
            catImage="image" in m["categories"],
            availableEN=False
        ), musicData)

    musics = merge_data(musicEN, musicJP)
    session.add_all(musics)
    print(f"Imported {len(musics)} musics.")

    # Import Music Difficulty
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'musicDifficulties.json'), 'r', encoding="utf8") as f:
        difficultyData: List[Dict] = json.load(f)
        difficultiesEN = map(lambda d: MusicDifficulty(
            id=d["id"],
            music=d["musicId"],
            difficulty=d["musicDifficulty"],
            playLevel=d["playLevel"],
            totalNoteCount=d["totalNoteCount"]
        ), difficultyData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'musicDifficulties.json'), 'r', encoding="utf8") as f:
        difficultyData: List[Dict] = json.load(f)
        difficultiesJP = map(lambda d: MusicDifficulty(
            id=d["id"],
            music=d["musicId"],
            difficulty=d["musicDifficulty"],
            playLevel=d["playLevel"],
            totalNoteCount=d["totalNoteCount"]
        ), difficultyData)

    difficulties = merge_data(difficultiesEN, difficultiesJP)
    session.add_all(difficulties)
    print(f"Imported {len(difficulties)} music difficulties.")

    # Import Honors
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'honors.json'), 'r', encoding="utf8") as f:
        honorData: List[Dict] = json.load(f)
        honorsEN = map(lambda h: Honor(
            id=h["id"],
            seq=h["seq"],
            groupId=h["groupId"],
            name=h["name"],
            honorRarity=h.get("honorRarity"),
            assetbundleName=h.get("assetbundleName"),
            honorMissionType=h.get("honorMissionType")
        ), honorData)
        honorLevelsEN = map(lambda l: HonorLevel(
            id=f'{l["honorId"]}-{l["level"]}',
            honorId=l["honorId"],
            level=l["level"],
            bonus=l["bonus"],
            description=l["description"],
            honorRarity=l.get("honorRarity"),
            assetbundleName=l.get("assetbundleName")
        ), [l for ls in map(lambda h: h["levels"], honorData) for l in ls])

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'honors.json'), 'r', encoding="utf8") as f:
        honorData: List[Dict] = json.load(f)
        honorsJP = map(lambda h: Honor(
            id=h["id"],
            seq=h["seq"],
            groupId=h["groupId"],
            name=h["name"],
            honorRarity=h.get("honorRarity"),
            assetbundleName=h.get("assetbundleName"),
            honorMissionType=h.get("honorMissionType")
        ), honorData)
        honorLevelsJP = map(lambda l: HonorLevel(
            id=f'{l["honorId"]}-{l["level"]}',
            honorId=l["honorId"],
            level=l["level"],
            bonus=l["bonus"],
            description=l["description"],
            honorRarity=l.get("honorRarity"),
            assetbundleName=l.get("assetbundleName")
        ), [l for ls in map(lambda h: h["levels"], honorData) for l in ls])

    honors = merge_data(honorsEN, honorsJP)
    honorLevels = merge_data(honorLevelsEN, honorLevelsJP)
    session.add_all(honors)
    session.add_all(honorLevels)
    print(f"Imported {len(honors)} honors with {len(honorLevels)} levels.")

    # Import Honor Groups
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'honorGroups.json'), 'r', encoding="utf8") as f:
        honorGroupData: List[Dict] = json.load(f)
        honorGroupsEN = map(lambda g: HonorGroup(
            id=g["id"],
            name=g["name"],
            honorType=g["honorType"],
            backgroundAssetbundleName=g.get("backgroundAssetbundleName"),
            frameName=g.get("frameName")
        ), honorGroupData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'honorGroups.json'), 'r', encoding="utf8") as f:
        honorGroupData: List[Dict] = json.load(f)
        honorGroupsJP = map(lambda g: HonorGroup(
            id=g["id"],
            name=g["name"],
            honorType=g["honorType"],
            backgroundAssetbundleName=g.get("backgroundAssetbundleName"),
            frameName=g.get("frameName")
        ), honorGroupData)

    honorGroups = merge_data(honorGroupsEN, honorGroupsJP)
    session.add_all(honorGroups)
    print(f"Imported {len(honorGroups)} honor groups.")

    session.commit()
    session.close()


def update_data():
    fetch_data()
    import_data()


if __name__ == "__main__":
    update_data()
