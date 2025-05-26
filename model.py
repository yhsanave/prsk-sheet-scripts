from typing import Dict, List, Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from enum import Enum


class Base(DeclarativeBase):
    pass


class Attributes(Enum):
    COOL = "cool"
    CUTE = "cute"
    HAPPY = "happy"
    MYSTERIOUS = "mysterious"
    PURE = "pure"


class Rarity(Enum):
    ONE = "rarity_1"
    TWO = "rarity_2"
    THREE = "rarity_3"
    FOUR = "rarity_4"
    BIRTHDAY = "rarity_birthday"


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


class Unit(Base):
    __tablename__ = 'units'

    unit: Mapped[str] = mapped_column(String(14), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    unitName: Mapped[str] = mapped_column(String(30))

    characters: Mapped[List["GameCharacter"]] = relationship()


class GameCharacter(Base):
    __tablename__ = 'gameCharacters'

    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[Optional[str]] = mapped_column(String(30))
    givenName: Mapped[str] = mapped_column(String(30))
    gender: Mapped[str] = mapped_column(String(30))
    unit: Mapped["Unit"] = mapped_column(ForeignKey("units.unit"))


class Skill(Base):
    __tablename__ = 'skills'

    id: Mapped[int] = mapped_column(primary_key=True)
    skillType: Mapped[SkillType] = mapped_column(Integer)

    def parse_skill_type(s: Dict) -> SkillType:
        effects: List[Dict] = s["skillEffects"]

        if s["skillFilterId"] == 1:
            return SkillType.SCORER
        elif s["skillFilterId"] == 3:
            return SkillType.PERFECT_LOCKER
        elif s["skillFilterId"] == 4:
            return SkillType.HEALER
        elif len(effects) == 2 and effects[0]["skillEffectType"] == "life_recovery" and effects[1]["activateNotesJudgementType"] == "perfect":
            return SkillType.BIRTHDAY_SCORER
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


class Card(Base):
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    prefix: Mapped[str] = mapped_column(String(100))
    character: Mapped["GameCharacter"] = mapped_column(
        ForeignKey("gameCharacters.id"))
    cardRarityType: Mapped[Rarity] = mapped_column(String(15))
    attribute: Mapped[Attributes] = mapped_column(String(10))
    supportUnit: Mapped[Optional["Unit"]] = mapped_column(
        ForeignKey("units.unit"))
    skill: Mapped["Skill"] = mapped_column(ForeignKey("skills.id"))
    releaseAt: Mapped[Date] = mapped_column(Date)
    assetBundleName: Mapped[str] = mapped_column(String(12))

    def get_thumbnail_url(self):
        return f'https://storage.sekai.best/sekai-jp-assets/thumbnail/chara/{self.assetBundleName}_normal.webp'


class MusicArtist(Base):
    __tablename__ = 'musicArtists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Music(Base):
    __tablename__ = 'musics'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    # categories: Mapped[List[str]] = mapped_column(List[str])
    title: Mapped[str] = mapped_column(String(200))
    creatorArtist: Mapped[Optional["MusicArtist"]] = mapped_column(
        ForeignKey('musicArtists.id'))
    lyricist: Mapped[str] = mapped_column(String(100))
    composer: Mapped[str] = mapped_column(String(100))
    arranger: Mapped[str] = mapped_column(String(100))
    assetBundleName: Mapped[str] = mapped_column(String(12))
    publishedAt: Mapped[Date] = mapped_column(Date)
    releasedAt: Mapped[Date] = mapped_column(Date)
    fillerSec: Mapped[float] = mapped_column(Float)

    difficulties: Mapped[List["MusicDifficulty"]] = relationship()

    def get_jacket_url(self):
        return f'https://storage.sekai.best/sekai-en-assets/music/jacket/{self.assetbundleName}/{self.assetbundleName}.webp'


class MusicDifficulty(Base):
    __tablename__ = 'musicDifficulties'

    id: Mapped[int] = mapped_column(primary_key=True)
    music: Mapped["Music"] = mapped_column(ForeignKey('musics.id'))
    difficulty: Mapped[str] = mapped_column(String(20))
    playLevel: Mapped[int] = mapped_column(Integer)
    totalNoteCount: Mapped[int] = mapped_column(Integer)
