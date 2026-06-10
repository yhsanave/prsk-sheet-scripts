from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from model import *
import csv

# Database Setup
engine = create_engine(config.DATABASE_STRING)
Session = sessionmaker(bind=engine)
session = Session()

fixtures = session.execute(
    select(MySekaiFixture)
    .order_by(MySekaiFixture.id)
).scalars().all()

talks = session.execute(
    select(MySekaiCharacterTalk)
    .join(MySekaiCharacterTalkConditionGroup, MySekaiCharacterTalk.mysekaiCharacterTalkConditionGroupId == MySekaiCharacterTalkConditionGroup.groupId)
    .join(MySekaiCharacterTalkCondition, MySekaiCharacterTalkConditionGroup.mysekaiCharacterTalkConditionId == MySekaiCharacterTalkCondition.id)
    .where(MySekaiCharacterTalkCondition.mysekaiCharacterTalkConditionType == MySekaiCharacterTalkConditionType.FIXTURE.value)
).scalars().all()

grid = {}
for f in fixtures:
    grid[f.id] = {
        "Fixture": f.name,
        "Reactions": ["FALSE"] * 56
    }

for t in talks:
    if t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId1:
        grid[t.mysekaiCharacterTalkConditionGroup.mysekaiCharacterTalkCondition.mysekaiCharacterTalkConditionTypeValue][
            "Reactions"][t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId1-1] = "TRUE"
    if t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId2:
        grid[t.mysekaiCharacterTalkConditionGroup.mysekaiCharacterTalkCondition.mysekaiCharacterTalkConditionTypeValue][
            "Reactions"][t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId2-1] = "TRUE"
    if t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId3:
        grid[t.mysekaiCharacterTalkConditionGroup.mysekaiCharacterTalkCondition.mysekaiCharacterTalkConditionTypeValue][
            "Reactions"][t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId3-1] = "TRUE"
    if t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId4:
        grid[t.mysekaiCharacterTalkConditionGroup.mysekaiCharacterTalkCondition.mysekaiCharacterTalkConditionTypeValue][
            "Reactions"][t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId4-1] = "TRUE"
    if t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId5:
        grid[t.mysekaiCharacterTalkConditionGroup.mysekaiCharacterTalkCondition.mysekaiCharacterTalkConditionTypeValue][
            "Reactions"][t.mysekaiGameCharacterUnitGroup.gameCharacterUnitId5-1] = "TRUE"

with open(os.path.join("output","mysekai-react-grid.csv"), "w+", encoding="utf8") as f:
    print("Fixture,Ichika,Saki,Honami,Shiho,Minori,Haruka,Airi,Shizuku,Kohane,An,Akito,Toya,Tsukasa,Emu,Nene,Rui,Kanade,Mafuyu,Ena,Mizuki,VS Miku,VS Rin,VS Len,VS Luka,VS Meiko,VS Kaito,LN Miku,MMJ Miku,VBS Miku,WxS Miku,N25 Miku,LN Rin,MMJ Rin,VBS Rin,WxS Rin,N25 Rin,LN Len,MMJ Len,VBS Len,WxS Len,N25 Len,LN Luka,MMJ Luka,VBS Luka,WxS Luka,N25 Luka,LN Meiko,MMJ Meiko,VBS Meiko,WxS Meiko,N25 Meiko,LN Kaito,MMJ Kaito,VBS Kaito,WxS Kaito,N25 Kaito", file=f)
    for r in grid.values():
        if any(map(lambda x: x == "TRUE", r["Reactions"])):
            row = ','.join([r["Fixture"], *r["Reactions"]])
            print(row, file=f)
