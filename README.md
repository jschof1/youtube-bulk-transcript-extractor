# youtube-bulk-transcript-extractor
Free Python tool to bulk extract YouTube transcripts. No Apify subscription needed - extract 100s of video transcripts in minutes.

## Features

- ✅ **100% Free** - No Apify subscription required
- ⚡ **Fast** - Extract hundreds of transcripts in minutes using parallel processing
- 🎯 **Simple** - Just provide video IDs and go
- 📊 **Multiple Output Formats** - JSON, CSV, or individual text files
- 🌍 **Multi-language** - Support for any language available on YouTube
- ⏱️ **Optional Timestamps** - Include timestamps in transcripts
- 🔧 **Customizable** - Adjust parallel workers for your system

## Installation

```bash
# Clone the repository
git clone https://github.com/OmarElsafy/youtube-bulk-transcript-extractor.git
cd youtube-bulk-transcript-extractor

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Extract Solana Breakpoint 2025 Transcripts (197 videos)

This repo includes all 197 video IDs from Solana Breakpoint 2025 conference:

```bash
# Extract all transcripts to JSON
python extract_transcripts.py breakpoint_2025_video_ids.txt

# Extract to individual text files
python extract_transcripts.py breakpoint_2025_video_ids.txt -f txt

# Extract with timestamps
python extract_transcripts.py breakpoint_2025_video_ids.txt -t
```

### Extract From Custom Video IDs

```bash
# Single video
python extract_transcripts.py dQw4w9WgXcQ

# Multiple videos (space-separated)
python extract_transcripts.py dQw4w9WgXcQ abc123def45

# From a text file (one video ID per line)
python extract_transcripts.py my_video_ids.txt
```

## Usage

```
python extract_transcripts.py [video_ids] [options]

Arguments:
  video_ids              Space-separated video IDs or path to text file

Options:
  -o, --output          Output file/directory name (default: transcripts_TIMESTAMP)
  -f, --format          Output format: json, csv, or txt (default: json)
  -w, --workers         Number of parallel workers (default: 10)
  -t, --timestamps      Include timestamps in transcripts
  -l, --lang            Language code (default: en)
```

## Examples

```bash
# Extract 10 videos to CSV with timestamps
python extract_transcripts.py video_ids.txt -f csv -t -o my_transcripts

# Use 20 parallel workers for faster extraction
python extract_transcripts.py video_ids.txt -w 20

# Extract Spanish transcripts
python extract_transcripts.py video_ids.txt -l es
```

## Output Formats

### JSON (default)
All transcripts in one JSON file with metadata:
```json
[
  {
    "video_id": "dQw4w9WgXcQ",
    "transcript": "Full transcript text...",
    "status": "success",
    "error": null
  }
]
```

### CSV
Spreadsheet-friendly format:
```csv
video_id,transcript,status,error
dQw4w9WgXcQ,"Full transcript text...",success,
```

### TXT
Separate text file for each video:
```
transcripts/
  ├── dQw4w9WgXcQ.txt
  ├── abc123def45.txt
  └── ...
```

## Why This Tool?

Apify's transcript extraction service costs money. This tool provides the same functionality:
- No subscription fees
- No rate limits
- Completely open source
- Easy to customize

## License

MIT License - See LICENSE file for details

## Author

Omar Elsafy

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.
