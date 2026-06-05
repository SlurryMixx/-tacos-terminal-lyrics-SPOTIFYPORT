#!/usr/bin/env python3

# ┌─────────────────────────────────────────────────────┐
# │  CONFIG — edit these                                │
# ├─────────────────────────────────────────────────────┤
# │  PLAYER       spotify player name for playerctl     │
# │  MARGIN       horizontal padding (cols)             │
# │  FIRE_HEIGHT  fire zone as fraction of screen       │
# │  REFRESH      render interval in seconds            │
# │  ACCENT       note/wait color  (r,g,b)              │
# │  GREEN        drug-word color  (r,g,b)              │
# │  DRUG_WORDS   set of words that trigger green       │
# ├─────────────────────────────────────────────────────┤
# │  DO NOT EDIT below unless you know what you're doing│
# └─────────────────────────────────────────────────────┘

PLAYER      = "spotify"
MARGIN      = 4
FIRE_HEIGHT = 0.6
REFRESH     = 0.08

ACCENT_RGB  = (180, 120, 255)
GREEN_RGB   = (80, 220, 80)

DRUG_WORDS = {
    "drug","drugs","weed","lean","codeine","xan","xans","xanax",
    "perc","percs","molly","coke","crack","dope","smoke","smokin",
    "smoking","high","stoned","lit","blunt","joint","plug","pack",
    "pressed","pill","pills","fent","fentanyl","syrup","cup",
    "dirty","actavis","promethazine","addy","addies","shrooms","acid",
    "roll","rollin","rolling","powder","lines","snort","snorting",
    "trippin","tripping","herb","kush","gas","loud","reefer",
}

import subprocess, threading, time, sys, os, re, signal
import urllib.request, urllib.parse, json, unicodedata, random
from typing import Optional

HIDE  = "\033[?25l"
SHOW  = "\033[?25h"
CLEAR = "\033[2J\033[H"
BOLD  = "\033[1m"
RST   = "\033[0m"

def mv(r,c):    return f"\033[{r};{c}H"
def fg(r,g,b):  return f"\033[38;2;{r};{g};{b}m"

WHITE  = fg(255,255,255)
ACCENT = fg(*ACCENT_RGB)
GREEN  = fg(*GREEN_RGB)

MINI_FONT = {
    'A':["▄▀▄","█▀█","▀ ▀"],'B':["█▀▄","█▀▄","▀▀ "],'C':["▄▀▀","█  ","▀▀▀"],
    'D':["█▀▄","█ █","▀▀ "],'E':["█▀▀","█▀ ","▀▀▀"],'F':["█▀▀","█▀ ","▀  "],
    'G':["▄▀▀","█ ▀","▀▀▀"],'H':["█ █","█▀█","▀ ▀"],'I':["█","█","▀"],
    'J':[" █"," █","▀ "],'K':["█ █","█▀ ","▀ ▀"],'L':["█  ","█  ","▀▀▀"],
    'M':["█▄▀▄█","█ ▀ █","▀   ▀"],'N':["█▄█","█ █","▀ ▀"],'O':["▄▀▀▄","█  █","▀▀▀ "],
    'P':["█▀▄","█▀ ","▀  "],'Q':["▄▀▀▄","█ ▀█","▀▀ ▀"],'R':["█▀▄","█▀▄","▀ ▀"],
    'S':["▄▀▀"," ▀▄","▀▀ "],'T':["▀█▀"," █ "," ▀ "],'U':["█ █","█ █","▀▀▀"],
    'V':["█ █","█ █"," ▀ "],'W':["█   █","█ ▄ █","▀▀▀▀▀"],'X':["█ █"," ▀ ","▀ ▀"],
    'Y':["█ █"," ▀ "," ▀ "],'Z':["▀▀█"," █ ","█▀▀"],' ':["   ","   ","   "],
    '0':["▄▀▀▄","█  █","▀▀▀ "],'1':["▄█ "," █ ","▀▀▀"],'2':["▀▀▄","▄▀ ","▀▀▀"],
    '3':["▀▀▄"," ▀▄","▀▀ "],'4':["█ █","▀▀█","  ▀"],'5':["█▀▀","▀▀▄","▀▀ "],
    '6':["▄▀▀","█▀▄","▀▀ "],'7':["▀▀█","  █"," ▀ "],'8':["▄▀▄","▄▀▄","▀▀ "],
    '9':["▄▀▄","▀▀█","▀▀ "],'!':["█","█","▀"],'?':["▀▄"," █","▀ "],
    '.':["  "," ","▀"],',':[" "," ","▄"],"'":["█","  ","  "],
    '-':["   ","▀▀▀","   "],'\u2019':["█","  ","  "],'\u2018':["█","  ","  "],
}
FH = 3

FIRE_CHARS  = [" ",".",":","^","*","x","s","S","#","♪","♫","♬"]
FIRE_COLORS = [
    (20,20,40),(40,10,60),(80,20,80),(120,20,100),
    (160,40,40),(200,80,20),(220,140,20),(240,200,60),
    (255,240,180),(255,255,255),
]

INSTRUMENTAL_MARKERS = {
    "","♪","🎵","🎶","♩","♫","instrumental","music",
    "[instrumental]","[music]","[intro]","[outro]",
    "[bridge]","[interlude]","[break]","[solo]",
}

def dw(text):
    w = 0
    for c in text:
        w += 2 if unicodedata.east_asian_width(c) in ('W','F') else 1
    return w

def wrap(text, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur+" "+w).strip()
        if dw(t) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]

def is_inst(text):
    t = text.lower().strip()
    return t in INSTRUMENTAL_MARKERS or bool(re.match(r"^\[.*\]$", t))

def strip_tags(text):
    return re.sub(r"^\[.*?\]\s*", "", text).strip()

def is_drug(word):
    return word.lower().strip("'.,!?") in DRUG_WORDS

def glyph_w(ch):
    g = MINI_FONT.get(ch, ["?"])
    return max(dw(r) for r in g) + 1

def render_block(text, maxw):
    words = text.split()
    line_groups, cur, cw = [], [], 0
    sp_w = glyph_w(' ')
    for word in words:
        uw = word.upper()
        ww = sum(glyph_w(c) for c in uw)
        sw = sp_w if cur else 0
        if cw + sw + ww > maxw and cur:
            line_groups.append(cur); cur = [word]; cw = ww
        else:
            cur.append(word); cw += sw + ww
    if cur: line_groups.append(cur)
    out = []
    for group in line_groups:
        rows = [""] * FH
        for wi, word in enumerate(group):
            col = GREEN if is_drug(word) else WHITE
            if wi > 0:
                for i,g in enumerate(MINI_FONT[' ']): rows[i] += WHITE+g+" "
            for ch in word.upper():
                glyph = MINI_FONT.get(ch, MINI_FONT.get(' ',["   "]*FH))
                for i,g in enumerate(glyph): rows[i] += col+g+" "
        out.extend(r+RST for r in rows)
        out.append("")
    return out

def fetch_lrclib(artist, title):
    p = urllib.parse.urlencode({"artist_name": artist, "track_name": title})
    try:
        req = urllib.request.Request(f"https://lrclib.net/api/get?{p}", headers={"User-Agent":"lrcpop/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            d = json.loads(r.read())
            return d.get("syncedLyrics") or d.get("plainLyrics")
    except: return None

def fetch_syncedlyrics(artist, title):
    try:
        r = subprocess.run(["syncedlyrics", f"{artist} - {title}"], capture_output=True, text=True, timeout=8)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None
    except: return None

def parse_lrc(lrc):
    pat = re.compile(r"\[(\d+):(\d+)\.(\d+)\](.*)")
    lines = []
    for line in lrc.splitlines():
        m = pat.match(line.strip())
        if m:
            mn,sc,cs,tx = m.groups()
            lines.append((int(mn)*60+int(sc)+int(cs)/100, tx.strip()))
    return sorted(lines)

def run_cmd(args, timeout=0.3):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else None
    except: return None

def get_track():
    raw = run_cmd(["playerctl","-p",PLAYER,"metadata","--format","{{artist}}|||{{title}}"], 2)
    if raw and "|||" in raw:
        p = raw.split("|||")
        if len(p)==2 and p[1]: return p[0].strip(), p[1].strip()
    return None

def get_pos():
    v = run_cmd(["playerctl","-p",PLAYER,"position"])
    try: return float(v) if v else None
    except: return None

def get_vol():
    v = run_cmd(["wpctl","get-volume","@DEFAULT_AUDIO_SINK@"])
    if v:
        m = re.search(r"([\d.]+)", v)
        if m: return min(1.0, float(m.group(1)))
    v = run_cmd(["pactl","get-sink-volume","@DEFAULT_SINK@"])
    if v:
        m = re.search(r"(\d+)%", v)
        if m: return min(1.0, int(m.group(1))/100)
    return 0.5 + 0.3*abs((time.time()%1.0)-0.5)

def term_size():
    try: sz = os.get_terminal_size(); return sz.lines, sz.columns
    except: return 40, 120

class Display:
    def __init__(self):
        self.lock       = threading.Lock()
        self.lines      = []
        self.idx        = -1
        self._fire      = None
        self._fr = self._fc = 0

    def set_lyrics(self, lines):
        with self.lock:
            self.lines = lines
            self.idx   = -1
            self._fire = None

    def _fire_init(self, fr, fc):
        self._fr, self._fc = fr, fc
        self._fire = [[0]*fc for _ in range(fr)]

    def _fire_step(self, intensity):
        fr, fc, grid = self._fr, self._fc, self._fire
        mx = len(FIRE_COLORS)-1
        bh = int(intensity*mx)
        for x in range(fc):
            grid[fr-1][x] = max(0, min(mx, bh+random.randint(-2,2))) if random.random()<intensity else max(0,grid[fr-1][x]-1)
        for y in range(fr-2,-1,-1):
            for x in range(fc):
                nx = max(0,min(fc-1,x+random.randint(-1,1)))
                grid[y][x] = max(0,grid[y+1][nx]-random.randint(0,2))

    def _draw_fire(self, out, rows, cols):
        fh  = max(4, int(rows*FIRE_HEIGHT))
        top = rows - fh
        if self._fire is None or self._fr!=fh or self._fc!=cols:
            self._fire_init(fh, cols)
        vol = get_vol()
        self._fire_step(vol)
        mx, cmx = len(FIRE_COLORS)-1, len(FIRE_CHARS)-1
        for y in range(fh):
            row = ""
            for x in range(cols):
                h = self._fire[y][x]
                if h == 0: row += " "
                else:
                    r2,g2,b2 = FIRE_COLORS[min(mx,h)]
                    row += fg(r2,g2,b2)+FIRE_CHARS[min(cmx,h)]+RST
            out.append(mv(top+y+1,1)+row)
        bar = "  ".join(["♪"]*max(1,int(vol*8)))
        out.append(mv(max(1,top-2), max(1,(cols-dw(bar))//2)) + ACCENT+BOLD+bar+RST)

    def render(self):
        rows, cols = term_size()
        pos = get_pos()
        with self.lock: lines = self.lines[:]

        new_idx = -1
        if pos is not None and lines:
            for i,(t,_) in enumerate(lines):
                if pos >= t: new_idx = i
        if new_idx != self.idx: self.idx = new_idx

        out = [CLEAR]
        usable = cols - MARGIN*2

        if not lines:
            msg = "♪  waiting for spotify  ♪"
            out.append(mv(rows//2, max(1,(cols-len(msg))//2)) + ACCENT+BOLD+msg+RST)
            sys.stdout.write("".join(out)); sys.stdout.flush(); return

        idx = self.idx
        cur = strip_tags(lines[idx][1]) if idx >= 0 else ""

        if is_inst(cur):
            self._draw_fire(out, rows, cols)
        else:
            block = render_block(cur, usable-2) if cur else None
            if block:
                bh = len(block)
                sr = max(1,(rows-bh)//2)
                for bi,brow in enumerate(block):
                    if not brow.strip(): continue
                    plain = re.sub(r'\033\[[^m]*m','',brow)
                    c = max(1,(cols-dw(plain))//2)
                    if sr+bi < rows: out.append(mv(sr+bi,c)+brow)
            else:
                wrapped = wrap(cur, usable)
                sr = max(1,(rows-len(wrapped))//2)
                for wi,wl in enumerate(wrapped):
                    colored = "".join((GREEN if is_drug(w) else WHITE)+w+" " for w in wl.split())
                    c = max(1,(cols-dw(wl))//2)
                    if sr+wi < rows: out.append(mv(sr+wi,c)+BOLD+colored+RST)

        sys.stdout.write("".join(out)); sys.stdout.flush()

class App:
    def __init__(self):
        self.display    = Display()
        self.last_track = None
        self.running    = True
        self.cache      = {}

    def fetch(self, artist, title):
        key = (artist, title)
        if key not in self.cache:
            self.cache[key] = fetch_lrclib(artist, title) or fetch_syncedlyrics(artist, title)
        return self.cache[key]

    def watcher(self):
        while self.running:
            track = get_track()
            if track and track != self.last_track:
                self.last_track = track
                lrc = self.fetch(*track)
                self.display.set_lyrics(parse_lrc(lrc) if lrc else [])
            time.sleep(1)

    def run(self):
        sys.stdout.write(HIDE+CLEAR); sys.stdout.flush()
        def bye(s=None,f=None):
            sys.stdout.write(SHOW+RST+CLEAR); sys.stdout.flush(); sys.exit(0)
        signal.signal(signal.SIGINT, bye)
        signal.signal(signal.SIGTERM, bye)
        threading.Thread(target=self.watcher, daemon=True).start()
        track = get_track()
        if track:
            self.last_track = track
            lrc = self.fetch(*track)
            self.display.set_lyrics(parse_lrc(lrc) if lrc else [])
        try:
            while True:
                self.display.render()
                time.sleep(REFRESH)
        except KeyboardInterrupt:
            bye()

if __name__ == "__main__":
    App().run()
