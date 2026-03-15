"""Frame Extractor — Extract representative frames from video candidates.

Lưu thumbnails/frames cho embeddings. Hỗ trợ graceful fallback nếu opencv chưa cài.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Extract representative frames from video files for embedding."""

    def __init__(self, cache_dir: str = "engine/data/media_cache/frames"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract_frames(self, video_path: str, num_frames: int = 3) -> list[str]:
        """Extract evenly-spaced frames from a video file.

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract (default 3)

        Returns:
            List of paths to extracted frame images
        """
        video_p = Path(video_path)
        if not video_p.exists():
            logger.warning("Video not found: %s", video_path)
            return []

        frame_dir = self.cache_dir / video_p.stem
        frame_dir.mkdir(parents=True, exist_ok=True)

        # Check cache
        existing = sorted(frame_dir.glob("frame_*.jpg"))
        if len(existing) >= num_frames:
            return [str(f) for f in existing[:num_frames]]

        try:
            return self._extract_with_opencv(str(video_p), str(frame_dir), num_frames)
        except ImportError:
            logger.info("OpenCV not available — trying PIL/moviepy fallback")
            return self._extract_fallback(str(video_p), str(frame_dir), num_frames)

    def _extract_with_opencv(self, video_path: str, output_dir: str, num_frames: int) -> list[str]:
        """Extract frames using OpenCV."""
        import cv2

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total <= 0:
            cap.release()
            return []

        interval = max(1, total // (num_frames + 1))
        frames = []

        for i in range(1, num_frames + 1):
            frame_pos = i * interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            ret, frame = cap.read()
            if ret:
                path = str(Path(output_dir) / f"frame_{i:03d}.jpg")
                cv2.imwrite(path, frame)
                frames.append(path)

        cap.release()
        return frames

    def _extract_fallback(self, video_path: str, output_dir: str, num_frames: int) -> list[str]:
        """Fallback frame extraction using moviepy or PIL."""
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            duration = clip.duration
            frames = []

            for i in range(1, num_frames + 1):
                t = (i / (num_frames + 1)) * duration
                path = str(Path(output_dir) / f"frame_{i:03d}.jpg")
                clip.save_frame(path, t=t)
                frames.append(path)

            clip.close()
            return frames
        except Exception as e:
            logger.warning("Frame extraction fallback failed: %s", e)
            return []

    def get_frame_count(self, video_path: str) -> int:
        """Get total frame count (if opencv available)."""
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            return count
        except Exception:
            return 0
