from __future__ import annotations


def estimate_quota(video_count: int, upload_thumbnail: bool, upload_captions: bool) -> int:
    total = video_count * 100
    if upload_thumbnail:
        total += video_count * 50
    if upload_captions:
        total += video_count * 400
    return total
