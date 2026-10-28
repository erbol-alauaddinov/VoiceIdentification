import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from speechbrain.inference.speaker import EncoderClassifier

SR = 16000
CHUNK_SEC = 15      # uzun audio shu uzunlikdagi bo'laklarga bo'linadi
MIN_CHUNK_SEC = 3   # bundan qisqa qoldiq tashlab yuboriladi
MAX_CHUNKS = 8      # bitta fayldan maksimal bo'lak soni


def to_wav16k(src: str, dst: str):
    """Istalgan audio formatni (mp3, ogg, m4a, wav, flac, opus...) 16kHz mono wav ga o'giradi."""
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", src, "-ac", "1", "-ar", str(SR), dst],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg xatosi: {src}")


class SpeakerEngine:
    def __init__(self, db_path: str | None = None, device: str | None = None):
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="pretrained_models/spkrec-ecapa-voxceleb",
            run_opts={"device": device},
        )
        self.names, self.embs, self.counts = None, None, {}
        if db_path:
            self.load_db(db_path)

    def load_db(self, path: str):
        data = np.load(path, allow_pickle=True)
        self.names = data["names"]
        self.embs = data["embs"]                 # (N, 192), normallashtirilgan
        self.counts = data["counts"].item()      # {ism: audio soni}

    @torch.no_grad()
    def _embed_wav(self, wav_path: str) -> np.ndarray:
        wav, sr = sf.read(wav_path, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        step = CHUNK_SEC * SR
        chunks = [wav[i:i + step] for i in range(0, len(wav), step)]
        chunks = [c for c in chunks if len(c) >= MIN_CHUNK_SEC * SR] or [wav]
        vecs = []
        for c in chunks[:MAX_CHUNKS]:
            t = torch.from_numpy(c).unsqueeze(0)
            e = self.model.encode_batch(t).squeeze().cpu().numpy()
            vecs.append(e / np.linalg.norm(e))
        m = np.mean(vecs, axis=0)
        return m / np.linalg.norm(m)

    def embed_file(self, path: str) -> np.ndarray:
        """Har qanday formatdagi audio fayldan embedding oladi."""
        with tempfile.TemporaryDirectory() as tmp:
            wav = str(Path(tmp) / "x.wav")
            to_wav16k(path, wav)
            return self._embed_wav(wav)

    def identify(self, path: str, top_k: int = 3):
        e = self.embed_file(path)
        scores = self.embs @ e
        order = np.argsort(-scores)[:top_k]
        return [(str(self.names[i]), float(scores[i])) for i in order]
