# PRSK Tracker Scripts

A collection of scripts and tools for supporting my Project Sekai stat tracking [spreadsheet](https://prsk-tracker.yhsanave.me).

## Setup

Run [setup.sh](./setup.sh) to create and activate the virtual environment, install dependencies, and pull the necessary sub-repositories.

Follow the instructions in the [gspread docs](https://docs.gspread.org/en/latest/oauth2.html#service-account) to set up a service account and save the `api-key.json` in the root folder.

Update `MASTER_SHEET_ID` in the config to point to your master sheet. Make sure the master sheet has the necessary worksheets created or it will throw an error when you try to update them.

## Updating the master sheet

Run [update-sheets.py](./update-sheets.py) to pull the latest data and update the sheets.

## Baked titles

In Project Sekai, titles consist of 2-4 separate layers in the following order from bottom to top:

| Name   | Purpose                                      | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------ | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| degree | The background of the title                  | ![Emu Fan](https://storage.sekai.best/sekai-en-assets/honor/honor_0054/degree_main.png)                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| frame  | The frame around the title                   | ![High Frame](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/frame_degree_m_3.png)                                                                                                                                                                                                                                                                                                                                                                                                                            |
| rank   | The tier in an event or scroll for FC titles | ![Top 7](https://storage.sekai.best/sekai-en-assets/honor/honor_top_000001/rank_main.png)                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| level  | The level pips or stars                      | ![Level 6 Pip](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/icon_degreeLv6.png)![Level Pip](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/icon_degreeLv.png)![Level Pip](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/icon_degreeLv.png)![Level Pip](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/icon_degreeLv.png)![Level Pip](https://raw.githubusercontent.com/yhsanave/prsk-sheet-assets/main/frame/icon_degreeLv.png) |

In-game, this allows common assets to be reused and combined efficiently, but this makes it difficult to use the images for other purposes. This is especially true in more limited contexts, such as google sheets.

Included in this repo are scripts for "baking" the titles into static images containing all of the component parts to be more easily used in these contexts.

To generate these images, first run [get-honor-images.py](./get-honor-images.py) to pull the degree images from [sekai.best](https://sekai.best). This will take a while the first time as it has to make a lot of requests to get the full list of available files and then download them all, but the directory will be cached in the [output](./output/) folder, so future runs will be faster and will only download new images.

Currently, there is no handling for new EN images previously downloaded from JP, so you will have to delete the JP images from [prsk-sheet-assets/honor](./prsk-sheet-assets/honor/) to get it to download again. Proper handling for that will come in a future update.

Once you have pulled the images, run [bake-honors.py](./bake-honors.py) to generate the baked images. These will be saved in [prsk-sheet-assets/honor_baked](./prsk-sheet-assets/honor_baked/) using the folder structure below. Note that `Title-Name` generally refers to the text on the title, with spaces replaced by dashes.

```bash

achievement                 # Titles for achievements
├── 0029-Real-Deal          # Format: ID-Title-Name
│   ├── main                # Full size titles
│   │   ├── 0000.png        # Greyed out version of the title, used in my spreadsheet to indicate an unearned title
│   │   └── Real-Deal.png   # For titles with only one level: Title-Name.png
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
├── 0036-I-Love-Them-All    # Format: HonorId-Title-Name
│   ├── main                # Full size titles
│   │   ├── 0000.png        # Greyed out version of the lowest level title, used in my spreadsheet to indicate an unearned title
│   │   └── 005.png         # For titles with multiple levels: the filename is the requirement for that level (e.g. CR5 on all characters = 005.png) 
│   │                       # Requirements are padded with leading 0s based on the longest level, such that all are the same length
│   │                       # Unearned title is always exactly 0000.png
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
└── ...

character                   # Character Rank titles
├── 14-Emu-Fan              # Format: CharacterId-Title-Name
│   ├── main                # Full size titles
│   │   ├── CR000.png       # Greyed out version of the title, used in my spreadsheet to indicate an unearned title
│   │   ├── CR005.png       # Format: CR{Level Requirement}.png, padded with leading 0s to 3 digits
│   │   └── ... 
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
└── ...

event                       # Event Ranking and BD/Anniv titles. Currently not used in my spreadsheet so these might change later
├── 0127-Smile-of-a-Dreamer # Format: HonorId-Title-Name
│   ├── main                # Full size titles
│   │   ├── 1st.png         # Format: Title-Name.png
│   │   └── ... 
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
├── 0166-Happy-Birthday...  # Format: HonorId-Title-Name
│   ├── main                # Full size titles
│   │   ├── Happy-Birth...  # Format: Title-Name.png
│   │   └── ... 
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
└── ...

rank_match                  # Titles for ranked season placements. Currently not used in my spreadsheet so these might change later
├── 0217-Ranked-Matches...  # Format: HonorId-Title-Name
│   ├── main                # Full size titles
│   │   ├── Gold-Class...   # Format: Title-Name.png
│   │   └── ... 
│   └── sub                 # Sub size titles
│       └── ...             # Same structure as main
└── ...
```
