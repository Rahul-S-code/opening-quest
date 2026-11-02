#!/usr/bin/env python3
"""Record Grandpa Rook's fixed lines with ElevenLabs.

  python3 record.py samples --voices ID[,ID...]      # short sample per voice -> samples/<name>.mp3
  python3 record.py lines --voice ID --out DIR [--only italian,ruy] [--limit N] [--model eleven_multilingual_v2]

lines.json comes from harvest.js (every fixed sentence, split the way the page splits it).
Each sentence becomes DIR/<fnv1a-hash>.mp3, and DIR/manifest.json lists the hashes. The page's vkey() uses the
same hash, so any sentence with a file plays the recording and everything else falls back to the browser voice.
Re-running skips files that exist, so a run that stops can be resumed. Needs TTS_API_KEY.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error, re
HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api.elevenlabs.io/v1'
FORMAT = 'mp3_44100_64'
SETTINGS = {'stability': 0.55, 'similarity_boost': 0.8, 'style': 0.25, 'use_speaker_boost': True, 'speed': 0.92}

def vkey(t):
    t = re.sub(r'\s+', ' ', t.strip()); h = 0x811c9dc5
    b = t.encode('utf-16-le')
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i+1] << 8); h = (h * 0x01000193) & 0xffffffff
    return '%08x' % h

def key():
    k = os.environ.get('TTS_API_KEY')
    if not k: sys.exit('TTS_API_KEY is not set')
    return k

def tts(text, voice, model, prev=None, nxt=None):
    body = {'text': text, 'model_id': model, 'voice_settings': SETTINGS}
    if prev: body['previous_text'] = prev
    if nxt: body['next_text'] = nxt
    req = urllib.request.Request(f'{API}/text-to-speech/{voice}?output_format={FORMAT}', json.dumps(body).encode(),
                                 {'xi-api-key': key(), 'Content-Type': 'application/json', 'Accept': 'audio/mpeg'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: return r.read()
        except urllib.error.HTTPError as e:
            msg = e.read()[:300].decode('utf-8', 'replace')
            if e.code in (429, 500, 502, 503) and attempt < 4: time.sleep(2 ** (attempt + 1)); continue
            sys.exit(f'HTTP {e.code}: {msg}')
        except urllib.error.URLError:
            if attempt < 4: time.sleep(2 ** (attempt + 1)); continue
            raise

SAMPLE = ("Ah, there you are, my young friend! Come, sit with me by the board. Today we'll learn the Italian Game, "
          "one of the oldest openings in chess. Your first mission: put a pawn right in the middle of the board. "
          "Splendid move! See how that pawn opens a door for your bishop and your queen? "
          "Now, Black wants the center too. Let's see what you do next. Take your time. A good chess player always thinks first.")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode', choices=['samples', 'lines'])
    ap.add_argument('--voices'); ap.add_argument('--voice'); ap.add_argument('--out', default=os.path.join(HERE, 'audio'))
    ap.add_argument('--only'); ap.add_argument('--limit', type=int); ap.add_argument('--model', default='eleven_multilingual_v2')
    a = ap.parse_args()
    if a.mode == 'samples':
        os.makedirs(os.path.join(HERE, 'samples'), exist_ok=True)
        for v in a.voices.split(','):
            f = os.path.join(HERE, 'samples', f'{v}-{a.model}.mp3')
            open(f, 'wb').write(tts(SAMPLE, v, a.model)); print('wrote', f, len(SAMPLE), 'chars')
        return
    lines = json.load(open(os.path.join(HERE, 'lines.json')))
    if a.only:
        want = set(a.only.split(',')); lines = [x for x in lines if want & set(x['src'])]
    os.makedirs(a.out, exist_ok=True)
    todo = [x for x in lines if not os.path.exists(os.path.join(a.out, vkey(x['s']) + '.mp3'))]
    if a.limit: todo = todo[:a.limit]
    print(f'{len(lines)} sentences selected, {len(todo)} to record, {sum(len(x["s"]) for x in todo)} chars')
    for i, x in enumerate(todo):
        data = tts(x['s'], a.voice, a.model)
        open(os.path.join(a.out, vkey(x['s']) + '.mp3'), 'wb').write(data)
        if i % 50 == 0: print(i, x['s'][:60], flush=True)
    files = sorted(f[:-4] for f in os.listdir(a.out) if f.endswith('.mp3'))
    json.dump({'voice': a.voice, 'model': a.model, 'format': FORMAT, 'files': files}, open(os.path.join(a.out, 'manifest.json'), 'w'))
    print('manifest', len(files), 'files')

if __name__ == '__main__': main()
