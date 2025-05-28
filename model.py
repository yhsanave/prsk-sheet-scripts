from typing import Dict, List, Optional
from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
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


class Unit(Base):
    __tablename__ = 'units'

    unit: Mapped[str] = mapped_column(String(14), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    unitName: Mapped[str] = mapped_column(String(30))

    characters: Mapped[List["GameCharacter"]
                       ] = relationship(back_populates='unit')


class GameCharacter(Base):
    __tablename__ = 'gameCharacters'

    id: Mapped[int] = mapped_column(primary_key=True)
    firstName: Mapped[Optional[str]] = mapped_column(String(30))
    givenName: Mapped[str] = mapped_column(String(30))
    gender: Mapped[str] = mapped_column(String(30))
    unitId: Mapped[str] = mapped_column(ForeignKey("units.unit"))
    unit: Mapped["Unit"] = relationship(back_populates='characters')


class Skill(Base):
    __tablename__ = 'skills'

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
    __tablename__ = 'cardSupplies'

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
    __tablename__ = 'cards'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    prefix: Mapped[str] = mapped_column(String(100))
    characterId: Mapped[int] = mapped_column(ForeignKey("gameCharacters.id"))
    character: Mapped["GameCharacter"] = relationship()
    cardRarityType: Mapped[Rarity] = mapped_column(String(15))
    attribute: Mapped[Attributes] = mapped_column(String(10))
    supportUnitId: Mapped[Optional[str]] = mapped_column(
        ForeignKey("units.unit"))
    supportUnit: Mapped[Optional["Unit"]] = relationship()
    skillId: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    skill: Mapped["Skill"] = relationship()
    releaseAt: Mapped[Date] = mapped_column(Date)
    assetBundleName: Mapped[str] = mapped_column(String(12))
    cardSupplyId: Mapped[int] = mapped_column(ForeignKey('cardSupplies.id'))
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
            "Subgroup": self.supportUnit.unitName if self.supportUnit is not None else None,
            "Attribute": str(Attributes(self.attribute)),
            "Rarity": str(Rarity(self.cardRarityType)),
            "Release Date": str(self.releaseAt),
            "Availability": str(self.cardSupply),
            "Skill": str(SkillType(self.skill.skillType)),
            "Thumbnail URL Normal": self.get_thumbnail_url(False),
            "Available on EN": self.availableEN,
            "Has Side Stories": len(self.sideStories) > 0,
            "Thumbnail URL Trained": self.get_thumbnail_url(True),
        }

    def to_row(self) -> List:
        return list(self.asdict().values())

    def get_row_headers(self) -> List[str]:
        return list(self.asdict().keys())
    
class CardEpisode(Base):
    __tablename__ = 'cardEpisodes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    cardId: Mapped[int] = mapped_column(ForeignKey('cards.id'))


class MusicArtist(Base):
    __tablename__ = 'musicArtists'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __hash__(self):
        return self.id


class MusicTag(Base):
    __tablename__ = 'musicTags'

    id: Mapped[int] = mapped_column(primary_key=True)
    musicId: Mapped[int] = mapped_column(ForeignKey('musics.id'))
    musicTag: Mapped[MusicTags] = mapped_column(String(20))
    seq: Mapped[int] = mapped_column(Integer)

    def __hash__(self):
        return self.id


class Music(Base):
    __tablename__ = 'musics'

    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    assetBundleName: Mapped[str] = mapped_column(String(12))
    publishedAt: Mapped[Date] = mapped_column(Date)
    releasedAt: Mapped[Date] = mapped_column(Date)
    fillerSec: Mapped[float] = mapped_column(Float)
    availableEN: Mapped[bool] = mapped_column(Boolean)

    creatorArtistId: Mapped[Optional[int]] = mapped_column(
        ForeignKey('musicArtists.id'))
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

    def __hash__(self):
        return self.id

    def get_jacket_url(self):
        return f'https://storage.sekai.best/sekai-en-assets/music/jacket/{self.assetBundleName}/{self.assetBundleName}.webp'

    def get_difficulty(self, diff: Difficulty):
        diffs = [d for d in self.difficulties if d.difficulty == diff]
        if diffs:
            return diffs[0]
        return None

    def get_diff_stats(self) -> Dict:
        levels = {
            f'{Difficulty(d.difficulty)} LV': d.playLevel for d in self.difficulties}
        notes = {
            f'{Difficulty(d.difficulty)} Notes': d.totalNoteCount for d in self.difficulties}
        
        if len(levels) < 6:
            levels["Append LV"] = ''
            notes["Append Notes"] = ''
        
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
            "Available on EN": self.availableEN,
            **self.get_diff_stats()
        }

    def to_row(self) -> List:
        return list(self.asdict().values())

    def get_row_headers(self) -> List[str]:
        return list(self.asdict().keys())


class MusicDifficulty(Base):
    __tablename__ = 'musicDifficulties'

    id: Mapped[int] = mapped_column(primary_key=True)
    music: Mapped["Music"] = mapped_column(ForeignKey('musics.id'))
    difficulty: Mapped[Difficulty] = mapped_column(String(20))
    playLevel: Mapped[int] = mapped_column(Integer)
    totalNoteCount: Mapped[int] = mapped_column(Integer)

    def __hash__(self):
        return self.id


class Gacha(Base):
    __tablename__ = 'gachas'

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
    __tablename__ = 'gachaDetails'

    id: Mapped[int] = mapped_column(primary_key=True)
    gacha: Mapped[Gacha] = mapped_column(ForeignKey('gachas.id'))
    card: Mapped[Card] = mapped_column(ForeignKey('cards.id'))
    weight: Mapped[int] = mapped_column(Integer)
    isWish: Mapped[bool] = mapped_column(Boolean)

    def __hash__(self):
        return self.id


class GachaPickup(Base):
    __tablename__ = 'gachaPickups'

    id: Mapped[int] = mapped_column(primary_key=True)
    gacha: Mapped["Gacha"] = mapped_column(ForeignKey('gachas.id'))
    card: Mapped["Card"] = mapped_column(ForeignKey('cards.id'))
    gachaPickupType: Mapped[str] = mapped_column(String(20))

    def __hash__(self):
        return self.id
