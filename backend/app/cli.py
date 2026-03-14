from __future__ import annotations

import argparse
from pathlib import Path

from .config import settings
from .db import init_db, stats
from .pipeline import enqueue_batch, run_workers
from .profiles import list_profiles, load_profile, sync_profiles
from .utils import require_bin


def main() -> None:
    parser = argparse.ArgumentParser(description="YouTube Auto V3")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check environment and print detected configuration")
    sub.add_parser("profiles", help="List available channel profiles")
    sub.add_parser("stats", help="Print job counts by state")

    enqueue = sub.add_parser("enqueue", help="Create jobs in SQLite queue")
    enqueue.add_argument("--profile", required=True)
    enqueue.add_argument("--count", type=int, default=10)
    enqueue.add_argument("--niche", type=str, default=None)
    enqueue.add_argument("--topic-file", type=Path, default=None)
    enqueue.add_argument("--format", type=str, choices=["shorts", "long"], default="shorts")
    enqueue.add_argument("--seed-url-file", type=Path, default=None)
    enqueue.add_argument("--youtube-url-file", type=Path, default=None)

    worker = sub.add_parser("worker", help="Process queued jobs")
    worker.add_argument("--profile", default=None)
    worker.add_argument("--limit", type=int, default=10)

    batch = sub.add_parser("batch", help="Enqueue then immediately process jobs")
    batch.add_argument("--profile", required=True)
    batch.add_argument("--count", type=int, default=10)
    batch.add_argument("--niche", type=str, default=None)
    batch.add_argument("--topic-file", type=Path, default=None)
    batch.add_argument("--format", type=str, choices=["shorts", "long"], default="shorts")
    batch.add_argument("--seed-url-file", type=Path, default=None)
    batch.add_argument("--youtube-url-file", type=Path, default=None)
    batch.add_argument("--worker-limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "doctor":
        init_db()
        sync_profiles()
        require_bin("ffmpeg")
        require_bin("ffprobe")
        print("profiles:", ", ".join(list_profiles()))
        print("db:", settings.db_path)
        print("output:", settings.output_root)
        print("cache:", settings.cache_root)
        print("openai_keys:", len(settings.openai_api_keys))
        print("elevenlabs_keys:", len(settings.elevenlabs_api_keys))
        print("pexels:", bool(settings.pexels_api_key))
        print("pixabay:", bool(settings.pixabay_api_key))
        print("upload_to_youtube:", settings.upload_to_youtube)
        return

    if args.command == "profiles":
        init_db()
        sync_profiles()
        print("\n".join(list_profiles()))
        return

    if args.command == "stats":
        init_db()
        print(stats())
        return

    if args.command in {"enqueue", "batch"}:
        profile = load_profile(args.profile)
        init_db()
        job_ids = enqueue_batch(
            profile=profile,
            count=args.count,
            niche=args.niche,
            topic_file=args.topic_file,
            video_format=args.format,
            seed_url_file=args.seed_url_file,
            youtube_url_file=args.youtube_url_file,
        )
        print(f"enqueued={len(job_ids)} ids={job_ids[:10]}{'...' if len(job_ids) > 10 else ''}")
        if args.command == "enqueue":
            return
        run_workers(channel=profile.name, limit=args.worker_limit)
        return

    if args.command == "worker":
        init_db()
        run_workers(channel=args.profile, limit=args.limit)
        return


if __name__ == "__main__":
    main()
