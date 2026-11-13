---
name: ukytsum
description: "Summarize a YouTube video into a markdown file in ~/Data/Docs/youtube-summaries/. Use when the user sends a YouTube URL and wants the summary saved to a file. For a chat-only summary or raw transcript, use youtube-content."
version: 3.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [YouTube, summary, markdown]
    related_skills: [youtube-content]
---

# ukytsum

One YouTube URL becomes one faithful markdown summary in `~/Data/Docs/youtube-summaries/`. Scratch files go to `~/.hermes/cache/scratch/`.

## Steps

1. **Route.** Continue when the user wants the summary saved as a file. Hand a chat-only summary or a raw-transcript request to `youtube-content`. Done when the route is decided.
2. **Metadata.** Run:
   ```bash
   yt-dlp --no-playlist --skip-download --print '%(id)s|%(channel,uploader)s|%(release_date,upload_date)s|%(duration_string)s|%(title)s' "<URL>"
   ```
   The fields are video_id, creator, upload date (`YYYYMMDD`, write it as `YYYY-MM-DD`), runtime and title; the title is everything after the fourth `|`. Done when all five are filled. If yt-dlp errors, report the error and stop.
3. **Duplicate check.** Run `grep -l 'video_id: "<video_id>"' ~/Data/Docs/youtube-summaries/*.md`, and check whether the target filename from step 6 already exists. If either matches, report the existing file and stop.
4. **Transcript.** Fetch with the `youtube-content` helper:
   ```bash
   python ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py "<URL>" --text-only --timestamps --language <chain> > ~/.hermes/cache/scratch/<video_id>.txt
   ```
   Pick a language chain that fits the video (`id,en,ms` for Indonesian). Done when the file is non-empty, holds no `{"error": ...}` object and is in the video's language. Retries follow `youtube-content` Error Handling, fetched plainly without proxies or cookies. If captions are disabled or retries run out, report and stop. For a video over 30 minutes, split it into 5-minute chunks with real time ranges: `python3 ~/.hermes/skills/ukytsum/scripts/transcript_chapters.py ~/.hermes/cache/scratch/<video_id>.txt --minutes 5`.
5. **Summarize.** Read the whole transcript, chunk by chunk. Write the body in the video's language:
   - an opening paragraph with the exact title, channel, runtime, language and speakers;
   - term definitions, each as `What is **X** means?` followed by a tab and the explanation;
   - thematic `##` sections;
   - concise takeaways.

   Stay with what the speakers say, keep their claims apart from verified facts, and keep their stated uncertainty. You may delegate the draft to a subagent that reads the scratch transcript. Review its draft before writing. Done when every part above is present and every chunk is covered.
6. **Write.** Create `~/Data/Docs/youtube-summaries/` if it is missing, then write one file named exactly `<creator> - <title>_<upload date>.md`, e.g. `Creator Name - Example Video Title_2026-03-02.md`. In creator and title, replace each of `/ \ : * ? " < > |` and control characters with `-`, collapse repeated spaces, and trim trailing dots and spaces. Start the file with this frontmatter, every value in double quotes with inner `"` and `\` backslash-escaped:
   ```yaml
   ---
   title: "<exact YouTube title>"
   creator: "<creator>"
   video_id: "<video_id>"
   upload_date: "YYYY-MM-DD"
   summary_date: "<today, local date>"
   source: "https://www.youtube.com/watch?v=<video_id>"
   language: "<summary language code, e.g. id>"
   ---
   ```
   Done when the file exists and its frontmatter parses.
7. **Clean up.** Delete this run's scratch files (`~/.hermes/cache/scratch/<video_id>*`). Report the file path.
