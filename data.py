import json
import os
from datetime import datetime
from typing import Dict, Iterable, List

from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from model import (Base, Card, CardEpisode, CardSupply, GameCharacter, GameCharacterUnit, Honor,
                   HonorGroup, HonorLevel, Music, MusicArtist, MusicDifficulty,
                   MusicOriginal, MusicTag, MySekaiBlueprint, MySekaiCharacterTalk,
                   MySekaiCharacterTalkCondition, MySekaiCharacterTalkConditionGroup, MySekaiCharacterTalkPreAction,
                   MySekaiCharacterTalkTweet, MySekaiFixture, MySekaiFixtureTag, MySekaiGameCharacterUnitGroup,
                   Skill, Unit)


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
    Base.metadata.drop_all(engine, [Base.metadata.tables[t]
                           for t in Base.metadata.tables if t.startswith('data_')])
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

    # Import Game Character Units
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'gameCharacterUnits.json'), 'r', encoding="utf8") as f:
        characterUnitData: List[Dict] = json.load(f)
        characterUnits = map(lambda c: GameCharacterUnit(
            id=c["id"],
            gameCharacterId=c["gameCharacterId"],
            unitName=c["unit"],
            colorCode=c["colorCode"],
            skinColorCode=c["skinColorCode"],
            skinShadowColorCode1=c["skinShadowColorCode1"],
            skinShadowColorCode2=c["skinShadowColorCode2"]
        ), characterUnitData)

    session.add_all(characterUnits)
    print(f"Imported {len(characterUnitData)} game character units.")

    # Import Skills
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'skills.json'), 'r', encoding="utf8") as f:
        skillData: List[Dict] = json.load(f)
        skillsEN = map(lambda s: Skill(
            id=s["id"],
            skillType=Skill.parse_skill_type(s).value  # type: ignore
        ), skillData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'skills.json'), 'r', encoding="utf8") as f:
        skillData: List[Dict] = json.load(f)
        skillsJP = map(lambda s: Skill(
            id=s["id"],
            skillType=Skill.parse_skill_type(s).value  # type: ignore
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

    # Import MySEKAI Fixture Tags
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiFixtureTags.json'), 'r', encoding="utf8") as f:
        mySekaiFixtureTagsData: List[Dict] = json.load(f)
        mySekaiFixtureTagsEN = map(lambda t: MySekaiFixtureTag(
            id=t["id"],
            name=t["name"],
            pronunciation=t["pronunciation"],
            mySekaiFixtureTagType=t["mysekaiFixtureTagType"],
            externalId=t.get("externalId", None)
        ), mySekaiFixtureTagsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiFixtureTags.json'), 'r', encoding="utf8") as f:
        mySekaiFixtureTagsData: List[Dict] = json.load(f)
        mySekaiFixtureTagsJP = map(lambda t: MySekaiFixtureTag(
            id=t["id"],
            name=t["name"],
            pronunciation=t["pronunciation"],
            mySekaiFixtureTagType=t["mysekaiFixtureTagType"],
            externalId=t.get("externalId", None)
        ), mySekaiFixtureTagsData)

    mySekaiFixtureTags = merge_data(mySekaiFixtureTagsEN, mySekaiFixtureTagsJP)
    session.add_all(mySekaiFixtureTags)
    print(f"Imported {len(mySekaiFixtureTags)} MySEKAI Fixture Tags")

    # Import MySEKAI Fixtures
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiFixtures.json'), 'r', encoding="utf8") as f:
        mySekaiFixturesData: List[Dict] = json.load(f)
        mySekaiFixturesEN = map(lambda f: MySekaiFixture(
            id=f["id"],
            seq=f["seq"],
            mysekaiFixtureType=f["mysekaiFixtureType"],
            name=f["name"],
            pronunciation=f["pronunciation"],
            flavorText=f["flavorText"],
            gridWidth=f["gridSize"]["width"],
            gridDepth=f["gridSize"]["depth"],
            gridHeight=f["gridSize"]["height"],
            mysekaiFixtureMainGenreId=f["mysekaiFixtureMainGenreId"],
            mysekaiFixtureSubGenreId=f.get("mysekaiFixtureSubGenreId"),
            mysekaiFixtureHandleType=f["mysekaiFixtureHandleType"],
            mysekaiSettableSiteType=f["mysekaiSettableSiteType"],
            mysekaiSettableLayoutType=f["mysekaiSettableLayoutType"],
            mysekaiFixturePutType=f["mysekaiFixturePutType"],
            mysekaiFixturePutSoundId=f["mysekaiFixturePutSoundId"],
            mysekaiFixtureFootstepId=f.get("mysekaiFixtureFootstepId"),
            isAssembled=f["isAssembled"],
            isDisassembled=f["isDisassembled"],
            mysekaiFixturePlayerActionType=f["mysekaiFixturePlayerActionType"],
            isGameCharacterAction=f["isGameCharacterAction"],
            assetbundleName=f["assetbundleName"],
            mysekaiFixtureTagId1=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId1"),
            mysekaiFixtureTagId2=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId2"),
            mysekaiFixtureTagId3=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId3"),
            mysekaiFixtureTagId4=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId4")
        ), mySekaiFixturesData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiFixtures.json'), 'r', encoding="utf8") as f:
        mySekaiFixturesData: List[Dict] = json.load(f)
        mySekaiFixturesJP = map(lambda f: MySekaiFixture(
            id=f["id"],
            seq=f["seq"],
            mysekaiFixtureType=f["mysekaiFixtureType"],
            name=f["name"],
            pronunciation=f["pronunciation"],
            flavorText=f["flavorText"],
            gridWidth=f["gridSize"]["width"],
            gridDepth=f["gridSize"]["depth"],
            gridHeight=f["gridSize"]["height"],
            mysekaiFixtureMainGenreId=f["mysekaiFixtureMainGenreId"],
            mysekaiFixtureSubGenreId=f.get("mysekaiFixtureSubGenreId"),
            mysekaiFixtureHandleType=f["mysekaiFixtureHandleType"],
            mysekaiSettableSiteType=f["mysekaiSettableSiteType"],
            mysekaiSettableLayoutType=f["mysekaiSettableLayoutType"],
            mysekaiFixturePutType=f["mysekaiFixturePutType"],
            mysekaiFixturePutSoundId=f["mysekaiFixturePutSoundId"],
            mysekaiFixtureFootstepId=f.get("mysekaiFixtureFootstepId"),
            isAssembled=f["isAssembled"],
            isDisassembled=f["isDisassembled"],
            mysekaiFixturePlayerActionType=f["mysekaiFixturePlayerActionType"],
            isGameCharacterAction=f["isGameCharacterAction"],
            assetbundleName=f["assetbundleName"],
            mysekaiFixtureTagId1=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId1"),
            mysekaiFixtureTagId2=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId2"),
            mysekaiFixtureTagId3=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId3"),
            mysekaiFixtureTagId4=f["mysekaiFixtureTagGroup"].get(
                "mysekaiFixtureTagId4")
        ), mySekaiFixturesData)

    mySekaiFixtures = merge_data(mySekaiFixturesEN, mySekaiFixturesJP)
    session.add_all(mySekaiFixtures)

    print(f"Imported {len(mySekaiFixtures)} MySEKAI Fixtures")

    # Import MySEKAI Blueprints
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiBlueprints.json'), 'r', encoding="utf8") as f:
        mySekaiBlueprintsData: List[Dict] = json.load(f)
        mySekaiBlueprintsEN = map(lambda b: MySekaiBlueprint(
            id=b["id"],
            mysekaiCraftType=b["mysekaiCraftType"],
            craftTargetId=b["craftTargetId"],
            isEnableSketch=b["isEnableSketch"],
            isObtainedByConvert=b["isObtainedByConvert"],
            craftCountLimit=b.get("craftCountLimit")
        ), mySekaiBlueprintsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiBlueprints.json'), 'r', encoding="utf8") as f:
        mySekaiBlueprintsData: List[Dict] = json.load(f)
        mySekaiBlueprintsJP = map(lambda b: MySekaiBlueprint(
            id=b["id"],
            mysekaiCraftType=b["mysekaiCraftType"],
            craftTargetId=b["craftTargetId"],
            isEnableSketch=b["isEnableSketch"],
            isObtainedByConvert=b["isObtainedByConvert"],
            craftCountLimit=b.get("craftCountLimit")
        ), mySekaiBlueprintsData)

    mySekaiBlueprints = merge_data(mySekaiBlueprintsEN, mySekaiBlueprintsJP)
    session.add_all(mySekaiBlueprints)
    print(f"Imported {len(mySekaiBlueprints)} MySEKAI Blueprints")

    # MySEKAI Character Talk Conditions
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiCharacterTalkConditions.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkConditionsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkConditionsEN = map(lambda c: MySekaiCharacterTalkCondition(
            id=c["id"],
            mysekaiCharacterTalkConditionType=c["mysekaiCharacterTalkConditionType"],
            mysekaiCharacterTalkConditionTypeValue=c["mysekaiCharacterTalkConditionTypeValue"]
        ), mySekaiCharacterTalkConditionsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiCharacterTalkConditions.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkConditionsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkConditionsJP = map(lambda c: MySekaiCharacterTalkCondition(
            id=c["id"],
            mysekaiCharacterTalkConditionType=c["mysekaiCharacterTalkConditionType"],
            mysekaiCharacterTalkConditionTypeValue=c["mysekaiCharacterTalkConditionTypeValue"]
        ), mySekaiCharacterTalkConditionsData)

    mySekaiCharacterTalkConditions = merge_data(
        mySekaiCharacterTalkConditionsEN, mySekaiCharacterTalkConditionsJP)
    session.add_all(mySekaiCharacterTalkConditions)
    print(
        f"Imported {len(mySekaiCharacterTalkConditions)} MySEKAI Character Talk Conditions")

    # MySEKAI Character Talk Tweets
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiCharacterTalkTweets.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkTweetsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkTweetsEN = map(lambda t: MySekaiCharacterTalkTweet(
            id=t["id"],
            motionName=t.get("motionName"),
            emoticonName=t.get("emoticonName"),
            expressionEyeName=t["expressionEyeName"],
            expressionMouthName=t["expressionMouthName"],
            text=t["text"]
        ), mySekaiCharacterTalkTweetsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiCharacterTalkTweets.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkTweetsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkTweetsJP = map(lambda t: MySekaiCharacterTalkTweet(
            id=t["id"],
            motionName=t.get("motionName"),
            emoticonName=t.get("emoticonName"),
            expressionEyeName=t["expressionEyeName"],
            expressionMouthName=t["expressionMouthName"],
            text=t["text"]
        ), mySekaiCharacterTalkTweetsData)

    mySekaiCharacterTalkTweets = merge_data(
        mySekaiCharacterTalkTweetsEN, mySekaiCharacterTalkTweetsJP)
    session.add_all(mySekaiCharacterTalkTweets)
    print(
        f"Imported {len(mySekaiCharacterTalkTweets)} MySEKAI Character Talk Tweets")

    # Import MySEKAI Character Talks
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiCharacterTalks.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalksData: List[Dict] = json.load(f)
        mySekaiCharacterTalksEN = map(lambda t: MySekaiCharacterTalk(
            id=t["id"],
            mysekaiGameCharacterUnitGroupId=t["mysekaiGameCharacterUnitGroupId"],
            mysekaiCharacterTalkConditionGroupId=t["mysekaiCharacterTalkConditionGroupId"],
            mysekaiSiteGroupId=t["mysekaiSiteGroupId"],
            mysekaiCharacterTalkTermId=t["mysekaiCharacterTalkTermId"],
            characterArchiveMysekaiCharacterTalkGroupId=t["characterArchiveMysekaiCharacterTalkGroupId"],
            assetbundleName=t["assetbundleName"],
            lua=t["lua"],
            isEnabledForMulti=t["isEnabledForMulti"]
        ), mySekaiCharacterTalksData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiCharacterTalks.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalksData: List[Dict] = json.load(f)
        mySekaiCharacterTalksJP = map(lambda t: MySekaiCharacterTalk(
            id=t["id"],
            mysekaiGameCharacterUnitGroupId=t["mysekaiGameCharacterUnitGroupId"],
            mysekaiCharacterTalkConditionGroupId=t["mysekaiCharacterTalkConditionGroupId"],
            mysekaiSiteGroupId=t["mysekaiSiteGroupId"],
            mysekaiCharacterTalkTermId=t["mysekaiCharacterTalkTermId"],
            characterArchiveMysekaiCharacterTalkGroupId=t["characterArchiveMysekaiCharacterTalkGroupId"],
            assetbundleName=t["assetbundleName"],
            lua=t["lua"],
            isEnabledForMulti=t["isEnabledForMulti"]
        ), mySekaiCharacterTalksData)

    mySekaiCharacterTalks = merge_data(
        mySekaiCharacterTalksEN, mySekaiCharacterTalksJP)
    session.add_all(mySekaiCharacterTalks)
    print(f"Imported {len(mySekaiCharacterTalks)} MySEKAI Character Talks")

    # Import MySEKAI Character Talk Pre-Actions
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiCharacterTalkPreActions.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkPreActionsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkPreActionsEN = map(lambda t: MySekaiCharacterTalkPreAction(
            id=t["id"],
            mysekaiCharacterTalkId=t["mysekaiCharacterTalkId"],
            mysekaiCharacterTalkTweetId=t["mysekaiCharacterTalkTweetId"]
        ), mySekaiCharacterTalkPreActionsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiCharacterTalkPreActions.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkPreActionsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkPreActionsJP = map(lambda t: MySekaiCharacterTalkPreAction(
            id=t["id"],
            mysekaiCharacterTalkId=t["mysekaiCharacterTalkId"],
            mysekaiCharacterTalkTweetId=t["mysekaiCharacterTalkTweetId"]
        ), mySekaiCharacterTalkPreActionsData)

    mySekaiCharacterTalkPreActions = merge_data(
        mySekaiCharacterTalkPreActionsEN, mySekaiCharacterTalkPreActionsJP)
    session.add_all(mySekaiCharacterTalkPreActions)
    print(
        f"Imported {len(mySekaiCharacterTalkPreActions)} MySEKAI Character Talk Pre-Actions")

    # Import MySEKAI Character Unit Groups
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiGameCharacterUnitGroups.json'), 'r', encoding="utf8") as f:
        mySekaiGameCharacterUnitGroupsData: List[Dict] = json.load(f)
        mySekaiGameCharacterUnitGroupsEN = map(lambda g: MySekaiGameCharacterUnitGroup(
            id=g["id"],
            gameCharacterUnitId1=g.get("gameCharacterUnitId1"),
            gameCharacterUnitId2=g.get("gameCharacterUnitId2"),
            gameCharacterUnitId3=g.get("gameCharacterUnitId3"),
            gameCharacterUnitId4=g.get("gameCharacterUnitId4"),
            gameCharacterUnitId5=g.get("gameCharacterUnitId5")
        ), mySekaiGameCharacterUnitGroupsData)

    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiGameCharacterUnitGroups.json'), 'r', encoding="utf8") as f:
        mySekaiGameCharacterUnitGroupsData: List[Dict] = json.load(f)
        mySekaiGameCharacterUnitGroupsJP = map(lambda g: MySekaiGameCharacterUnitGroup(
            id=g["id"],
            gameCharacterUnitId1=g.get("gameCharacterUnitId1"),
            gameCharacterUnitId2=g.get("gameCharacterUnitId2"),
            gameCharacterUnitId3=g.get("gameCharacterUnitId3"),
            gameCharacterUnitId4=g.get("gameCharacterUnitId4"),
            gameCharacterUnitId5=g.get("gameCharacterUnitId5")
        ), mySekaiGameCharacterUnitGroupsData)

    mySekaiGameCharacterUnitGroups = merge_data(
        mySekaiGameCharacterUnitGroupsEN, mySekaiGameCharacterUnitGroupsJP)
    session.add_all(mySekaiGameCharacterUnitGroups)
    print(
        f"Imported {len(mySekaiGameCharacterUnitGroups)} MySEKAI Game Character Unit Groups")

    # Import MySEKAI Character Talk Condition Groups
    with open(os.path.join(config.DATA_DIRECTORY_EN, 'mysekaiCharacterTalkConditionGroups.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkConditionGroupsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkConditionGroupsEN = map(lambda g: MySekaiCharacterTalkConditionGroup(
            id=g["id"],
            groupId=g["groupId"],
            mysekaiCharacterTalkConditionId=g["mysekaiCharacterTalkConditionId"]
        ), mySekaiCharacterTalkConditionGroupsData)

    with open(os.path.join(config.DATA_DIRECTORY_JP, 'mysekaiCharacterTalkConditionGroups.json'), 'r', encoding="utf8") as f:
        mySekaiCharacterTalkConditionGroupsData: List[Dict] = json.load(f)
        mySekaiCharacterTalkConditionGroupsJP = map(lambda g: MySekaiCharacterTalkConditionGroup(
            id=g["id"],
            groupId=g["groupId"],
            mysekaiCharacterTalkConditionId=g["mysekaiCharacterTalkConditionId"]
        ), mySekaiCharacterTalkConditionGroupsData)

    mySekaiCharacterTalkConditionGroups = merge_data(
        mySekaiCharacterTalkConditionGroupsEN, mySekaiCharacterTalkConditionGroupsJP)
    session.add_all(mySekaiCharacterTalkConditionGroups)
    print(
        f"Imported {len(mySekaiCharacterTalkConditionGroups)} MySEKAI Character Talk Condition Groups")

    session.commit()
    session.close()


def update_data():
    fetch_data()
    import_data()


if __name__ == "__main__":
    update_data()
