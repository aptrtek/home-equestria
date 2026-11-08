# Mare Fair

A mod for [Home: Equestria](https://github.com/homedevanon/home-equestria) that brings the five
[Mare Fair](https://marefair.org/mascots/) mascots to Ponyville. They gather at their own parked
balloon on Balloon Hill, keep daily schedules, and talk through the game's AI ponies.

Built for game version `0.3.0-maredev`. With the mod switched off, Ponyville is unchanged.

![The five Mare Fair mascots in game](docs/lineup.png)

## Download

- **[mare_fair.pck](https://github.com/aptrtek/home-equestria/releases/download/mare-fair-v1.0.0/mare_fair.pck)**: the mod itself. This is the only file players need.
- **[mare_fair_source.zip](https://github.com/aptrtek/home-equestria/releases/download/mare-fair-v1.0.0/mare_fair_source.zip)**: just the mod's source folder, for anyone who wants to change it.

## The mascots

| Pony | Race | Look | Character |
| --- | --- | --- | --- |
| **Fair Flyer** | Pegasus | Two-tone blonde mane and a big wavy tail, wide sun hat with a sunflower | Organises the event |
| **Soirée** | Earth pony | Rounded cyan bob with a level fringe, short crescent tail | Blunt and sardonic; Matinée's twin; married to aperture_tech |
| **Matinée** | Pegasus | Light-blue bob like her twin's, high ponytail in a pink scrunchie, tail fading to periwinkle | Bubbly costume enthusiast; Soirée's twin |
| **Morning Mimosa** | Earth pony | Green mane, leafy braids tied with oranges, round spiral glasses | Eccentric |
| **Fun Raiser** | Unicorn | Orange ponytail and curls with a pale streak, gold half-moon reading glasses | Introduces ponies who need something to each other |

Not on the models yet: their outfits, Fair Flyer's purple belly, Morning Mimosa's gold bangles,
and Fun Raiser's jacket and pendant.

## Install

1. Download [mare_fair.pck](https://github.com/aptrtek/home-equestria/releases/download/mare-fair-v1.0.0/mare_fair.pck).
2. Put it in your mods folder. **Settings → Mods → Open mods folder** opens it for you.
   On Windows that is `%APPDATA%\home-equestria-public\mods\`.
3. Restart the game. The mod is listed under **Settings → Mods**.

Mods are programs, so only install them from people you trust.

## Meeting them

They live at the Mare Fair balloon on Balloon Hill, a repainted copy of the town's balloon that stays parked. They take no houses in Ponyville, so nopony who lives there is moved or has to share. From the console you can also bring one to you:

```
spawn fair flyer
spawn soiree
spawn matinee
spawn morning mimosa
spawn fun raiser
```

## Talking to them

They use whichever AI you have set up on the game's **Dialogue & microphone** page. That includes
a free local model through [Ollama](https://ollama.com) (`http://127.0.0.1:11434/v1`).

The ponies know you by the `player_name` in your `ai_config.json`, which on Windows is in
`%APPDATA%\home-equestria-public\`. Soirée is married to aperture_tech. Anyone else gets the
honest version: she will tell them she is married, and turn them down.

## Working on the mod

You need the game's source project, the `source-data` zips from the matching release, and Godot
4.5 stable. `mods/README.md` covers the setup. Then:

```
# Run the game with the unpacked mod
godot --xr-mode off --path . -- --mod-src mare_fair

# Check the mascots are all present
godot --headless --xr-mode off --path . --script res://tools/mare_fair/check_mascots.gd -- --mod-src mare_fair

# Build the .pck
godot --headless --xr-mode off --path . --script res://tools/modding/build_mod.gd -- mare_fair
```

### Hair and accessories

Each mare's mane, tail and any accessories live in one file, `hair/<id>.glb`, built by
`hair/build_<id>_hair.py`. The scripts need Python with numpy. Each one edits its `.glb` in place
and reuses the skeleton already in the file, so the hair follows the game's head, neck and tail
bones.

```
python mods/mare_fair/hair/build_soiree_hair.py
```

Hats and glasses are modelled into the same file as the hair. Reopen the project afterwards so
Godot reimports the file.

## Credits

Mare Fair and its mascots belong to the convention and its artists. This is an unofficial fan
mod. Colours, bios, cutie marks and hair are based on the public art on
[marefair.org](https://marefair.org/mascots/). The cutie marks are that site's public vectors. The
reference pictures are not included. The 3D hair and accessories are original to this mod.
