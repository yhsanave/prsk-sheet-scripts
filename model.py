import datetime
from enum import Enum
import os
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import config


class Base(DeclarativeBase):
    pass


class Attributes(Enum):
    COOL = "cool"
    CUTE = "cute"
    HAPPY = "happy"
    MYSTERIOUS = "mysterious"
    PURE = "pure"

    def __str__(self):
        return self.value.title()


class Rarity(Enum):
    ONE = "rarity_1"
    TWO = "rarity_2"
    THREE = "rarity_3"
    FOUR = "rarity_4"
    BIRTHDAY = "rarity_birthday"

    def __str__(self):
        return {
            Rarity.ONE.value: '1',
            Rarity.TWO.value: '2',
            Rarity.THREE.value: '3',
            Rarity.FOUR.value: '4',
            Rarity.BIRTHDAY.value: 'BD',
        }.get(self.value)


class SkillType(Enum):
    SCORER = 1
    PERFECT_SCORER = 2
    HEALER = 3
    PERFECT_LOCKER = 4
    LIFE_SCORER = 5
    COMBO_SCORER = 6
    BIRTHDAY_SCORER = 7
    UNIT_SCORER = 8
    BLOOM_FES_SCORER = 9

    def __str__(self):
        return self.name.replace('_', ' ').title()


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXPERT = "expert"
    MASTER = "master"
    APPEND = "append"

    def __str__(self):
        return self.name.title()


class HonorRarity(Enum):
    LOW = "low"
    MIDDLE = "middle"
    HIGH = "high"
    HIGHEST = "highest"

    def __str__(self):
        return self.value.title()


class HonorType(Enum):
    ACHIEVEMENT = "achievement"
    CHARACTER = "character"
    EVENT = "event"
    RANK_MATCH = "rank_match"
    BIRTHDAY = "birthday"

    def __str__(self):
        return self.value.title()


class HonorMissionType(Enum):
    EASY_FC = "easy_full_combo"
    NORMAL_FC = "normal_full_combo"
    HARD_FC = "hard_full_combo"
    EXPERT_FC = "expert_full_combo"
    MASTER_FC = "master_full_combo"
    MASTER_AP = "master_full_perfect"

    def __str__(self):
        return self.name.title()


class MusicTags(Enum):
    ALL = 'all'
    VIRTUAL_SINGER = 'vocaloid'
    LEO_NEED = 'light_music_club'
    MORE_MORE_JUMP = 'idol'
    VIVID_BAD_SQUAD = 'street'
    WONDERLANDS_SHOWTIME = 'theme_park'
    NIGHTCORD = 'school_refusal'
    OTHER = 'other'

    def __str__(self):
        return {
            MusicTags.ALL.value: "All",
            MusicTags.VIRTUAL_SINGER.value: "VIRTUAL SINGER",
            MusicTags.LEO_NEED.value: "Leo/need",
            MusicTags.MORE_MORE_JUMP.value: "MORE MORE JUMP!",
            MusicTags.VIVID_BAD_SQUAD.value: "Vivid BAD SQUAD",
            MusicTags.WONDERLANDS_SHOWTIME.value: "Wonderlands×Showtime",
            MusicTags.NIGHTCORD.value: "Nightcord at 25:00",
            MusicTags.OTHER.value: "Other",
        }.get(self.value)


class HonorDirectoryType(Enum):
    HONOR = 'honor'
    HONOR_FRAME = 'honor_frame'
    RANK_LIVE = 'rank_live'

    def __str__(self):
        return self.value.title()

# Event Priority Constants
RARITY_EVENT_PRIORITY = [Rarity.FOUR, Rarity.BIRTHDAY,
                         Rarity.THREE, Rarity.TWO, Rarity.ONE]
SKILL_EVENT_PRIORITY = [SkillType.BLOOM_FES_SCORER, SkillType.UNIT_SCORER, SkillType.LIFE_SCORER, SkillType.COMBO_SCORER,
                        SkillType.PERFECT_SCORER, SkillType.SCORER, SkillType.PERFECT_LOCKER, SkillType.HEALER, SkillType.BIRTHDAY_SCORER]
EVENT_PRIORITY_TEXT_MAP = [
    '4⭐ BloomFes', '4⭐ U-Scorer', '4⭐ ColorFes', '4⭐ ColorFes', '4⭐ P-Scorer', '4⭐ Scorer', '4⭐ P-Locker', '4⭐ Healer', '4⭐ BD-Scorer',
    '🎀 BloomFes', '🎀 U-Scorer', '🎀 ColorFes', '🎀 ColorFes', '🎀 P-Scorer', '🎀 Scorer', '🎀 P-Locker', '🎀 Healer', '🎀 BD-Scorer',
    '3⭐ BloomFes', '3⭐ U-Scorer', '3⭐ ColorFes', '3⭐ ColorFes', '3⭐ P-Scorer', '3⭐ Scorer', '3⭐ P-Locker', '3⭐ Healer', '3⭐ BD-Scorer',
    '2⭐ BloomFes', '2⭐ U-Scorer', '2⭐ ColorFes', '2⭐ ColorFes', '2⭐ P-Scorer', '2⭐ Scorer', '2⭐ P-Locker', '2⭐ Healer', '2⭐ BD-Scorer',
    '1⭐ BloomFes', '1⭐ U-Scorer', '1⭐ ColorFes', '1⭐ ColorFes', '1⭐ P-Scorer', '1⭐ Scorer', '1⭐ P-Locker', '1⭐ Healer', '1⭐ BD-Scorer',
]


class Unit(Base):
    __tablename__ = 'data_units'

    unit: Mapped[str] = mapped_column(String(14), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    unitName: Mapped[str] = mapped_column(String(30))

    characters: Mapped[List["GameCharacter"]
                       ] = relationship(back_populates='unit')


class GameCharacter(Base):
    __tablename__ = 'data_gameCharacters'

    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[Optional[str]] = mapped_column(String(30))
    givenName: Mapped[str] = mapped_column(String(30))
    gender: Mapped[str] = mapped_column(String(30))
    unitId: Mapped[str] = mapped_column(ForeignKey('data_units.unit'))
    unit: Mapped["Unit"] = relationship(back_populates='characters')


class Skill(Base):
    __tablename__ = 'data_skills'

    id: Mapped[int] = mapped_column(primary_key=True)
    skillType: Mapped[SkillType] = mapped_column(Integer)

    def __hash__(self):
        return self.id

    def parse_skill_type(s: Dict) -> SkillType:
        effects: List[Dict] = s["skillEffects"]

        if s["skillFilterId"] == 1:
            return SkillType.SCORER
        elif len(effects) == 2 and effects[0]["skillEffectType"] == "life_recovery" and effects[1].get("activateNotesJudgmentType", None) == "perfect":
            return SkillType.BIRTHDAY_SCORER
        elif s["skillFilterId"] == 3:
            return SkillType.PERFECT_LOCKER
        elif s["skillFilterId"] == 4:
            return SkillType.HEALER
        elif effects[0]["skillEffectType"] == "score_up_condition_life":
            return SkillType.LIFE_SCORER
        elif effects[0]["skillEffectType"] == "score_up_keep":
            return SkillType.COMBO_SCORER
        elif effects[0]["activateNotesJudgmentType"] == "perfect":
            return SkillType.PERFECT_SCORER

        enhance: Dict = effects[0].get("skillEnhance", None)
        if enhance is not None and enhance.get("skillEnhanceType", None) == "sub_unit_score_up":
            return SkillType.UNIT_SCORER

        return SkillType.BLOOM_FES_SCORER


class CardSupply(Base):
    __tablename__ = 'data_cardSupplies'

    id: Mapped[int] = mapped_column(primary_key=True)
    cardSupplyType: Mapped[str] = mapped_column(String(30))

    def __str__(self):
        return {
            "normal": "Permanent",
            "birthday": "Birthday Limited",
            "term_limited": "Limited",
            "colorful_festival_limited": "Colorful Festival Limited",
            "bloom_festival_limited": "Bloom Festival Limited",
            "unit_event_limited": "Unit-Limited",
            "collaboration_limited": "Temporary"
        }.get(self.cardSupplyType, 'Unknown')

    def __hash__(self):
        return self.id


class Card(Base):
    __tablename__ = 'data_cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    prefix: Mapped[str] = mapped_column(String(100))
    characterId: Mapped[int] = mapped_column(ForeignKey('data_gameCharacters.id'))
    character: Mapped["GameCharacter"] = relationship()
    cardRarityType: Mapped[Rarity] = mapped_column(String(15))
    attribute: Mapped[Attributes] = mapped_column(String(10))
    supportUnitId: Mapped[Optional[str]] = mapped_column(
        ForeignKey('data_units.unit'))
    supportUnit: Mapped[Optional["Unit"]] = relationship()
    skillId: Mapped[int] = mapped_column(ForeignKey('data_skills.id'))
    skill: Mapped["Skill"] = relationship()
    releaseAt: Mapped[Date] = mapped_column(Date)
    assetBundleName: Mapped[str] = mapped_column(String(12))
    cardSupplyId: Mapped[int] = mapped_column(ForeignKey('data_cardSupplies.id'))
    cardSupply: Mapped["CardSupply"] = relationship()
    availableEN: Mapped[bool] = mapped_column(Boolean)
    sideStories: Mapped[List["CardEpisode"]] = relationship()

    def __hash__(self):
        return self.id

    def get_thumbnail_url(self, trained: bool):
        if trained and Rarity(self.cardRarityType) in [Rarity.ONE, Rarity.TWO, Rarity.BIRTHDAY]:
            return None
        return f'https://storage.sekai.best/sekai-jp-assets/thumbnail/chara/{self.assetBundleName}_{"after_training" if trained else "normal"}.webp'

    def asdict(self) -> Dict:
        return {
            "ID": self.id,
            "Seq": self.seq,
            "Card Name": self.prefix,
            "Character": f'{self.character.firstName} {self.character.givenName}' if self.character.firstName else self.character.givenName,
            "Group": self.character.unit.unitName,
            "Subgroup": self.supportUnit.unitName if self.supportUnit is not None else self.character.unit.unitName,
            "Attribute": str(Attributes(self.attribute)),
            "Rarity": str(Rarity(self.cardRarityType)),
            "Release Date": str(self.releaseAt),
            "Availability": str(self.cardSupply),
            "Skill": str(SkillType(self.skill.skillType)),
            "Thumbnail URL Normal": self.get_thumbnail_url(False),
            "Available on EN": self.availableEN,
            "Has Side Stories": len(self.sideStories) > 0,
            "Thumbnail URL Trained": self.get_thumbnail_url(True),
            **self.get_event_priority()
        }

    def to_row(self) -> List:
        return list(self.asdict().values())

    def get_row_headers(self) -> List[str]:
        return list(self.asdict().keys())

    def get_event_priority(self) -> Dict:
        '''Returns the event priority values as a dict for output to sheets. Used in Event Coverage table.'''

        priority = RARITY_EVENT_PRIORITY.index(Rarity(self.cardRarityType)) * len(
            SKILL_EVENT_PRIORITY) + SKILL_EVENT_PRIORITY.index(SkillType(self.skill.skillType))

        return {
            "Event Priority Int": priority,
            "Event Priority Str": f'{priority:03d}',
            "Event Priority Text": EVENT_PRIORITY_TEXT_MAP[priority]
        }


class CardEpisode(Base):
    __tablename__ = 'data_cardEpisodes'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    cardId: Mapped[int] = mapped_column(ForeignKey('data_cards.id'))


class MusicArtist(Base):
    __tablename__ = 'data_musicArtists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __hash__(self):
        return self.id


class MusicTag(Base):
    __tablename__ = 'data_musicTags'

    id: Mapped[int] = mapped_column(primary_key=True)
    musicId: Mapped[int] = mapped_column(ForeignKey('data_musics.id'))
    musicTag: Mapped[MusicTags] = mapped_column(String(20))
    seq: Mapped[int] = mapped_column(Integer)

    def __hash__(self):
        return self.id


class MusicOriginal(Base):
    __tablename__ = 'data_musicOriginals'

    id: Mapped[int] = mapped_column(primary_key=True)
    musicId: Mapped[int] = mapped_column(ForeignKey('data_musics.id'))
    videoLink: Mapped[str] = mapped_column(String(100))


class Music(Base):
    __tablename__ = 'data_musics'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    assetBundleName: Mapped[str] = mapped_column(String(12))
    publishedAt: Mapped[Date] = mapped_column(Date)
    releasedAt: Mapped[Date] = mapped_column(Date)
    fillerSec: Mapped[float] = mapped_column(Float)
    availableEN: Mapped[bool] = mapped_column(Boolean)

    creatorArtistId: Mapped[Optional[int]] = mapped_column(
        ForeignKey('data_musicArtists.id'))
    creatorArtist: Mapped[Optional["MusicArtist"]] = relationship()
    lyricist: Mapped[str] = mapped_column(String(100))
    composer: Mapped[str] = mapped_column(String(100))
    arranger: Mapped[str] = mapped_column(String(100))

    catMV: Mapped[bool] = mapped_column(Boolean)
    catMV2D: Mapped[bool] = mapped_column(Boolean)
    catOriginal: Mapped[bool] = mapped_column(Boolean)
    catImage: Mapped[bool] = mapped_column(Boolean)

    difficulties: Mapped[List["MusicDifficulty"]] = relationship()
    tags: Mapped[List["MusicTag"]] = relationship()
    videoLink: Mapped["MusicOriginal"] = relationship()

    def __hash__(self):
        return self.id

    def get_jacket_url(self):
        return f'https://storage.sekai.best/sekai-{"en" if self.availableEN else "jp"}-assets/music/jacket/{self.assetBundleName}/{self.assetBundleName}.webp'

    def get_difficulty(self, diff: Difficulty):
        diffs = [d for d in self.difficulties if d.difficulty == diff]
        if diffs:
            return diffs[0]
        return None

    def get_diff_stats(self) -> Dict:
        if not self.is_removed():
            levels = {
                f'{Difficulty(d.difficulty)} LV': d.playLevel for d in self.difficulties}
            notes = {
                f'{Difficulty(d.difficulty)} Notes': d.totalNoteCount for d in self.difficulties}
        else:
            levels = {}
            notes = {}

        # Default to empty strings for missing difficulties
        levels = {
            'Easy LV': levels.get('Easy LV', ''),
            'Normal LV': levels.get('Normal LV', ''),
            'Hard LV': levels.get('Hard LV', ''),
            'Expert LV': levels.get('Expert LV', ''),
            'Master LV': levels.get('Master LV', ''),
            'Append LV': levels.get('Append LV', '')
        }
        notes = {
            'Easy Notes': notes.get('Easy Notes', ''),
            'Normal Notes': notes.get('Normal Notes', ''),
            'Hard Notes': notes.get('Hard Notes', ''),
            'Expert Notes': notes.get('Expert Notes', ''),
            'Master Notes': notes.get('Master Notes', ''),
            'Append Notes': notes.get('Append Notes', '')
        }

        return {**levels, **notes}

    def get_units(self) -> List:
        return [str(MusicTags(t.musicTag)) for t in self.tags if t.musicTag != MusicTags.ALL.value]

    def asdict(self) -> Dict:
        return {
            "ID": self.id,
            "Seq": self.seq,
            "Title": self.title,
            "Unit": "\n".join(self.get_units()),
            "Producer": self.creatorArtist.name if self.creatorArtistId else self.composer,
            "Lyricist": self.lyricist,
            "Composer": self.composer,
            "Arranger": self.arranger,
            "Published": str(self.publishedAt),
            "Released": str(self.releasedAt),
            "Filler Sec": self.fillerSec,
            "Jacket URL": self.get_jacket_url(),
            "3D MV": self.catMV,
            "2D MV": self.catMV2D,
            "Original": self.catOriginal,
            "Image": self.catImage,
            "Available on EN": self.availableEN if not self.is_removed() else None,
            **self.get_diff_stats(),
            "Video Link": self.videoLink.videoLink if self.videoLink else None
        }

    def to_row(self) -> List:
        return list(self.asdict().values())

    def get_row_headers(self) -> List[str]:
        return list(self.asdict().keys())

    def is_removed(self) -> bool:
        '''Returns True if the song has been removed. Removed songs have no release date, so it gets set to 1969-12-31.'''
        return self.releasedAt < datetime.date(1970, 1, 1)


class MusicDifficulty(Base):
    __tablename__ = 'data_musicDifficulties'

    id: Mapped[int] = mapped_column(primary_key=True)
    music: Mapped["Music"] = mapped_column(ForeignKey('data_musics.id'))
    difficulty: Mapped[Difficulty] = mapped_column(String(20))
    playLevel: Mapped[int] = mapped_column(Integer)
    totalNoteCount: Mapped[int] = mapped_column(Integer)

    def __hash__(self):
        return self.id


class Gacha(Base):
    __tablename__ = 'data_gachas'

    id: Mapped[int] = mapped_column(primary_key=True)
    gachaType: Mapped[str] = mapped_column(String(10))
    name: Mapped[str] = mapped_column(String(100))
    seq: Mapped[int] = mapped_column(Integer)
    startAt: Mapped[Date] = mapped_column(Date)
    endAt: Mapped[Date] = mapped_column(Date)
    gachaDetails: Mapped[List["GachaDetail"]] = relationship()
    gachaPickups: Mapped[List["GachaPickup"]] = relationship()

    def __hash__(self):
        return self.id


class GachaDetail(Base):
    __tablename__ = 'data_gachaDetails'

    id: Mapped[int] = mapped_column(primary_key=True)
    gacha: Mapped[Gacha] = mapped_column(ForeignKey('data_gachas.id'))
    card: Mapped[Card] = mapped_column(ForeignKey('data_cards.id'))
    weight: Mapped[int] = mapped_column(Integer)
    isWish: Mapped[bool] = mapped_column(Boolean)

    def __hash__(self):
        return self.id


class GachaPickup(Base):
    __tablename__ = 'data_gachaPickups'

    id: Mapped[int] = mapped_column(primary_key=True)
    gacha: Mapped["Gacha"] = mapped_column(ForeignKey('data_gachas.id'))
    card: Mapped["Card"] = mapped_column(ForeignKey('data_cards.id'))
    gachaPickupType: Mapped[str] = mapped_column(String(20))

    def __hash__(self):
        return self.id


class HonorLevel(Base):
    __tablename__ = 'data_honorLevels'

    id: Mapped[str] = mapped_column(primary_key=True)
    honorId: Mapped[int] = mapped_column(ForeignKey('data_honors.id'))
    level: Mapped[int] = mapped_column(Integer)
    bonus: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(String(200))
    assetbundleName: Mapped[Optional[str]] = mapped_column(String(30))
    honorRarity: Mapped[Optional[HonorRarity]] = mapped_column(String(7))


class HonorGroup(Base):
    __tablename__ = 'data_honorGroups'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    honorType: Mapped[HonorType] = mapped_column(String(30))
    backgroundAssetbundleName: Mapped[Optional[str]] = mapped_column(
        String(50))
    frameName: Mapped[Optional[str]] = mapped_column(String(50))

    honors: Mapped[List["Honor"]] = relationship(back_populates='group')


class Honor(Base):
    __tablename__ = 'data_honors'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    groupId: Mapped[int] = mapped_column(ForeignKey('data_honorGroups.id'))
    group: Mapped[HonorGroup] = relationship(back_populates='honors')
    honorRarity: Mapped[Optional[HonorRarity]] = mapped_column(String(7))
    name: Mapped[str] = mapped_column(String(100))
    assetbundleName: Mapped[Optional[str]] = mapped_column(String(30))
    honorMissionType: Mapped[Optional[HonorMissionType]
                             ] = mapped_column(String(20))

    levels: Mapped[List[HonorLevel]] = relationship()


class HonorDirectory(Base):
    __tablename__ = 'sb_honorDirectory'

    directory: Mapped[str] = mapped_column(String(200), primary_key=True)
    availableEN: Mapped[bool] = mapped_column(Boolean)
    dirType: Mapped[HonorDirectoryType] = mapped_column(String(11))
    files: Mapped[List["HonorFile"]] = relationship(back_populates='directory')

class HonorFile(Base):
    __tablename__ = 'sb_honorPath'

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(100))
    directoryId: Mapped[str] = mapped_column(ForeignKey('sb_honorDirectory.directory'))
    directory: Mapped[HonorDirectory] = relationship(back_populates='files')
    downloadedEN: Mapped[bool] = mapped_column(Boolean)

    def get_path(self) -> str:
        return os.path.join(config.ASSETS_DIRECTORY, *self.directory.directory.split('/'), self.filename)

    def get_url(self) -> str:
        return f'https://storage.sekai.best/sekai-{"en" if self.directory.availableEN else "jp"}-assets/{self.directory.directory}{self.filename}'