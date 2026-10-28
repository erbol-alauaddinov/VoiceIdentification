"""
audios/ papkasidan ovoz bazasini yaratish.

Struktura:
    audios/
      Ali_Valiyev/   a1.wav  a2.mp3 ...
      Dilnoza/       x.ogg   y.m4a ...

Ishlatish:
    python build_db.py --root audios --out speakers_db.npz
"""
import argparse
from pathlib import Path

import numpy as np
from tqdm import tqdm

from speaker_engine import SpeakerEngine

EXTS = {".wav", ".mp3", ".ogg", ".oga", ".opus", ".m4a", ".flac", ".aac", ".wma", ".webm", ".mp4"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="audios")
    ap.add_argument("--out", default="speakers_db.npz")
    ap.add_argument("--max-files", type=int, default=30, help="bir shaxsdan maksimal fayl soni")
    args = ap.parse_args()

    root = Path(args.root)
    people = sorted(p for p in root.iterdir() if p.is_dir())
    if not people:
        raise SystemExit(f"'{root}' ichida shaxs papkalari topilmadi")

    engine = SpeakerEngine()
    names, embs, counts = [], [], {}

    for person in people:
        files = sorted(f for f in person.rglob("*") if f.suffix.lower() in EXTS)
        if not files:
            print(f"⚠️  {person.name}: audio yo'q, o'tkazib yuborildi")
            continue
        idx = np.linspace(0, len(files) - 1, min(args.max_files, len(files))).astype(int)
        vecs = []
        for i in tqdm(idx, desc=person.name, leave=False):
            try:
                vecs.append(engine.embed_file(str(files[i])))
            except Exception as e:
                print(f"⚠️  {files[i].name}: {e}")
        if not vecs:
            continue
        m = np.mean(vecs, axis=0)
        names.append(person.name)
        embs.append(m / np.linalg.norm(m))
        counts[person.name] = len(vecs)
        print(f"✅ {person.name}: {len(vecs)} ta audio")

    np.savez(args.out, names=np.array(names), embs=np.stack(embs).astype("float32"),
             counts=np.array(counts, dtype=object))
    print(f"\nSaqlandi: {args.out} ({len(names)} ta shaxs)")


if __name__ == "__main__":
    main()
