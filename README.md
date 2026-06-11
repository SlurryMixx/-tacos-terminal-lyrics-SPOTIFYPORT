[PLEASE READ]

/\ /\ /\ /\ /\ /\ /\ /

terminal lyrics visualizer for spotify. block font, fire particles during instrumentals, drug words go green (i found it a bit funny to add that), transparent background.

```
  ██      ██████   ██████ ██████   ██████  ██████
  ██      ██   ██ ██      ██   ██ ██    ██ ██   ██
  ██      ██████  ██      ██████  ██    ██ ██████
  ██      ██   ██ ██      ██      ██    ██ ██
  ███████ ██   ██  ██████ ██       ██████  ██
```

---

## dependencies

Required:

    python >= 3.12
    playerctl   — media player control via MPRIS (linux only)
    syncedlyrics — fallback lyrics source (optional but recommended)

---

## install

### linux (arch)

```bash
sudo pacman -S playerctl python
pip install syncedlyrics --break-system-packages
```

### linux (ubuntu/debian)

```bash
sudo apt install playerctl python3 python3-pip
pip install syncedlyrics --break-system-packages
```

### macos

playerctl doesn't exist on macOS. you'll need a shim.

```bash
brew install python
pip3 install syncedlyrics
```

then install [nowplaying-cli](https://github.com/kirtan-shah/nowplaying-cli):

```bash
brew install nowplaying-cli
```

edit the top of `lrcpop.py` and change:

```python
PLAYER = "spotify"
```

then in `get_track()` and `get_pos()`, replace the playerctl calls with:

```bash
nowplaying-cli get artist
nowplaying-cli get title
nowplaying-cli get elapsedTime
```

or just run the mac version (coming eventually lol)

### windows

playerctl doesn't work on windows either. closest option:

install [SMTC-cli](https://github.com/spmn/smtc-cli) or use WSL2 with ubuntu and follow the linux steps.

WSL2 is the easiest path:

```powershell
wsl --install
```

then follow the ubuntu steps inside WSL.

---

## run

```bash
python3 lrcpop.py
```

play something in spotify first. it auto-detects the current track, fetches lyrics from lrclib.net, and starts displaying.

---

## config

edit the top of `lrcpop.py`:

```python
PLAYER      = "spotify"   # playerctl player name
MARGIN      = 4           # horizontal padding
FIRE_HEIGHT = 0.6         # fire zone height (fraction of screen)
REFRESH     = 0.08        # render speed in seconds
ACCENT_RGB  = (180,120,255) # color for notes/waiting screen
GREEN_RGB   = (80,220,80)   # color for drug words
DRUG_WORDS  = { ... }     # words that trigger green — add your own
```

do not edit anything below the config block unless you know what you're doing.

---

## features

- auto-detects spotify via playerctl (MPRIS)
- fetches synced lyrics from lrclib.net, falls back to syncedlyrics
- block font that word-wraps to fit your terminal size
- drug/substance words render green
- fire particle animation during instrumentals, intensity driven by system volume
- seek/skip detection — jumps to correct lyric instantly
- transparent background — your wallpaper shows through

---

## notes

non-mainstream songs sometimes don't have lyrics on lrclib. if you get a blank screen, the song just isn't in the database yet.

volume detection uses `wpctl` (PipeWire) then falls back to `pactl`. if neither is found it pulses automatically.

---

## credits

inspired by and built on top of [tacos-terminal-lyrics](https://github.com/tacoproz1/tacos-terminal-lyrics) by tacoproz1.
font style, lrc tooling, and overall concept — all his. go check it out.

---

## license

MIT
