#!/usr/bin/env python3
"""
YouTube Bulk Transcript Extractor
A free alternative to Apify's transcript extraction service.

Extract transcripts from hundreds of YouTube videos in minutes.
No subscription fees, no rate limits, completely free and open source.

Author: Omar Elsafy
License: MIT
"""

import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


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
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
        
        if include_timestamps:
            transcript_text = '\n'.join([
                f"[{item['start']:.2f}s] {item['text']}"
                for item in transcript_list
            ])
        else:
            transcript_text = ' '.join([item['text'] for item in transcript_list])
        
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


def extract_bulk_transcripts(video_ids, max_workers=10, include_timestamps=False, lang='en'):
    """
    Extract transcripts from multiple videos in parallel.
    
    Args:
        video_ids (list): List of YouTube video IDs
        max_workers (int): Number of parallel workers
        include_timestamps (bool): Whether to include timestamps
        lang (str): Preferred language code
    
    Returns:
        list: List of transcript results
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_single_transcript, vid, include_timestamps, lang): vid
            for vid in video_ids
        }
        
        for future in tqdm(as_completed(futures), total=len(video_ids), desc="Extracting transcripts"):
            result = future.result()
            results.append(result)
    
    return results


def save_to_json(results, output_path):
    """Save results to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {output_path}")


def save_to_csv(results, output_path):
    """Save results to CSV file."""
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
    
    print(f"\n✅ Saved {len([r for r in results if r['status'] == 'success'])} files to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Extract YouTube transcripts in bulk - Free Apify alternative"
    )
    parser.add_argument(
        'video_ids',
        nargs='+',
        help='YouTube video IDs (space-separated) or path to text file with IDs'
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
        type=int,
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
    
    # Load video IDs
    if len(args.video_ids) == 1 and Path(args.video_ids[0]).is_file():
        with open(args.video_ids[0], 'r') as f:
            video_ids = [line.strip() for line in f if line.strip()]
    else:
        video_ids = args.video_ids
    
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
        save_to_json(results, f"{args.output}.json")
    elif args.format == 'csv':
        save_to_csv(results, f"{args.output}.csv")
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


if __name__ == '__main__':
    main()
