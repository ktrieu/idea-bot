import re
import html
import json

TITLE_REGEX = re.compile(r"<title>(.*)<\/title>")

if __name__ == "__main__":
    with open("titles.txt", "w", encoding="utf-8") as titles_file:
        with open("wp_dump.xml", "r", encoding="utf-8") as wp_dump_file:
            dump_file_text = wp_dump_file.read()
            seen = set()
            # XML parsing is for communists
            for match in re.findall(TITLE_REGEX, dump_file_text):
                if match == "":
                    continue
                if match in seen:
                    continue
                seen.add(match)
                cleaned_match = html.unescape(match.rstrip("\n"))
                # Output line by line in JSONL format
                titles_file.write(
                    json.dumps(
                        {
                            "prompt": "Looking for a mathNEWS article idea? How about:",
                            "completion": cleaned_match + "####",
                        }
                    )
                    + "\n"
                )
