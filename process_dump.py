import re
import html
import json

TITLE_REGEX = re.compile(r"<title>(.*)<\/title>")

if __name__ == "__main__":
    with open("titles.txt", "w", encoding="utf-8") as titles_file:
        with open("wp_dump.xml", "r", encoding="utf-8") as wp_dump_file:
            dump_file_text = wp_dump_file.read()
            # XML parsing is for communists
            for match in re.findall(TITLE_REGEX, dump_file_text):
                if match == "":
                    continue
                cleaned_match = html.unescape(match.rstrip("\n"))
                # Output line by line in JSONL format
                titles_file.write(
                    json.dumps({"prompt": "", "completion": cleaned_match}) + "\n"
                )
