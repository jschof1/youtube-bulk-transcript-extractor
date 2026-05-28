#!/usr/bin/env python3
"""
YouTube Bulk Transcript Extractor
A free alternative to Apify's transcript extraction service.

Extract transcripts from hundreds of YouTube videos in minutes.
No subscription fees, completely free and open source.

Author: Omar Elsafy
License: MIT
"""

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi


YOUTUBE_URL_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}


def positive_int(value):
    """Parse a positive integer for argparse."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def normalize_video_id(value):
    """Accept either a raw YouTube video ID or a common YouTube URL."""
    candidate = value.strip()
    if not candidate:
        return candidate

    url_candidate = candidate
    if "youtube.com/" in candidate or "youtu.be/" in candidate:
        if not candidate.startswith(("http://", "https://")):
            url_candidate = f"https://{candidate}"

        parsed = urlparse(url_candidate)
        host = parsed.netloc.lower()
        if host in YOUTUBE_URL_HOSTS:
            if host in {"youtu.be", "www.youtu.be"}:
                return parsed.path.strip("/").split("/")[0]

            if parsed.path == "/watch":
                return parse_qs(parsed.query).get("v", [candidate])[0]

            for prefix in ("/shorts/", "/embed/", "/live/"):
                if parsed.path.startswith(prefix):
                    return parsed.path[len(prefix):].split("/")[0]

    return candidate


def load_video_ids(inputs):
    """Load video IDs from command-line values or a one-ID-per-line file."""
    if len(inputs) == 1 and Path(inputs[0]).is_file():
        lines = Path(inputs[0]).read_text(encoding="utf-8").splitlines()
        video_ids = []
        for line in lines:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            video_id = normalize_video_id(line)
            if video_id:
                video_ids.append(video_id)
        return video_ids

    return [video_id for video_id in (normalize_video_id(value) for value in inputs) if video_id]


def transcript_item_text(item):
    """Read transcript text from both current and older API item shapes."""
    return item["text"] if isinstance(item, dict) else item.text


def transcript_item_start(item):
    """Read transcript start time from both current and older API item shapes."""
    return item["start"] if isinstance(item, dict) else item.start


def fetch_transcript(video_id, lang):
    """Fetch transcript using the installed youtube-transcript-api version."""
    api = YouTubeTranscriptApi()
    if hasattr(api, "fetch"):
        return api.fetch(video_id, languages=[lang])
    return YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])


def output_file_path(output, output_format):
    """Append the expected extension unless the user already supplied it."""
    path = Path(output)
    suffix = f".{output_format}"
    if path.suffix.lower() == suffix:
        return path
    return path.with_name(f"{path.name}{suffix}")


def extract_single_transcript(video_id, include_timestamps=False, lang='en'):
    """
    Extract transcript for a single video.
    
    Args:
        video_id (str): YouTube video ID
        include_timestamps (bool): Whether to include timestamps
        lang (str): Preferred language code
    
    Returns:
        dict: Transcript data with video_id, text, and optional timestamps
    """
    try:
        transcript_list = fetch_transcript(video_id, lang)
        
        if include_timestamps:
            transcript_text = '\n'.join([
                f"[{transcript_item_start(item):.2f}s] {transcript_item_text(item)}"
                for item in transcript_list
            ])
        else:
            transcript_text = ' '.join([transcript_item_text(item) for item in transcript_list])
        
        return {
            'video_id': video_id,
            'transcript': transcript_text,
            'status': 'success',
            'error': None
        }
    
    except Exception as e:
        return {
            'video_id': video_id,
            'transcript': None,
            'status': 'failed',
            'error': str(e)
        }


def extract_bulk_transcripts(
    video_ids,
    max_workers=10,
    include_timestamps=False,
    lang='en',
    show_progress=True,
):
    """
    Extract transcripts from multiple videos in parallel.
    
    Args:
        video_ids (list): List of YouTube video IDs
        max_workers (int): Number of parallel workers
        include_timestamps (bool): Whether to include timestamps
        lang (str): Preferred language code
        show_progress (bool): Whether to show a progress bar
    
    Returns:
        list: List of transcript results
    """
    results = [None] * len(video_ids)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_single_transcript, vid, include_timestamps, lang): index
            for index, vid in enumerate(video_ids)
        }
        
        for future in tqdm(
            as_completed(futures),
            total=len(video_ids),
            desc="Extracting transcripts",
            disable=not show_progress,
        ):
            index = futures[future]
            result = future.result()
            results[index] = result
    
    return results


def save_to_json(results, output_path):
    """Save results to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {output_path}")


def save_to_csv(results, output_path):
    """Save results to CSV file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['video_id', 'transcript', 'status', 'error'])
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✅ Saved to {output_path}")


def save_individual_files(results, output_dir):
    """Save each transcript as a separate text file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        if result['status'] == 'success':
            file_path = output_path / f"{result['video_id']}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result['transcript'])
    
    success_count = len([r for r in results if r['status'] == 'success'])
    print(f"\n✅ Saved {success_count} files to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Extract YouTube transcripts in bulk - Free Apify alternative"
    )
    parser.add_argument(
        'video_ids',
        nargs='+',
        help='YouTube video IDs/URLs (space-separated) or path to text file with IDs/URLs'
    )
    parser.add_argument(
        '-o', '--output',
        default=f'transcripts_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        help='Output file/directory name (default: transcripts_TIMESTAMP)'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'csv', 'txt'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '-w', '--workers',
        type=positive_int,
        default=10,
        help='Number of parallel workers (default: 10)'
    )
    parser.add_argument(
        '-t', '--timestamps',
        action='store_true',
        help='Include timestamps in transcripts'
    )
    parser.add_argument(
        '-l', '--lang',
        default='en',
        help='Language code (default: en)'
    )
    
    args = parser.parse_args()
    
    video_ids = load_video_ids(args.video_ids)
    if not video_ids:
        parser.error("No video IDs found. Provide at least one ID or a file with one ID per line.")
    
    print(f"🎬 Extracting transcripts for {len(video_ids)} videos...")
    print(f"⚙️  Workers: {args.workers} | Format: {args.format} | Lang: {args.lang}")
    
    # Extract transcripts
    results = extract_bulk_transcripts(
        video_ids,
        max_workers=args.workers,
        include_timestamps=args.timestamps,
        lang=args.lang
    )
    
    # Save results
    if args.format == 'json':
        save_to_json(results, output_file_path(args.output, args.format))
    elif args.format == 'csv':
        save_to_csv(results, output_file_path(args.output, args.format))
    elif args.format == 'txt':
        save_individual_files(results, args.output)
    
    # Summary
    success_count = len([r for r in results if r['status'] == 'success'])
    failed_count = len([r for r in results if r['status'] == 'failed'])
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    if failed_count > 0:
        print(f"\n⚠️  Failed video IDs:")
        for result in results:
            if result['status'] == 'failed':
                print(f"   - {result['video_id']}: {result['error']}")

    return 1 if failed_count and success_count == 0 else 0


if __name__ == '__main__':
    raise SystemExit(main())
