import re
import html
import json

TITLE_REGEX = re.compile(r"<title>(.*)<\/title>")
CDATA_REGEX = re.compile(r"<!\[CDATA\[(.*)\]\]>")

if __name__ == "__main__":
    with open("titles.txt", "w", encoding="utf-8") as titles_file:
        with open("wp_dump.xml", "r", encoding="utf-8") as wp_dump_file:
            dump_file_text = wp_dump_file.read()
            seen = set()
            total_tokens = 0
            # XML parsing is for communists
            for match in re.findall(TITLE_REGEX, dump_file_text):
                if match == "":
                    continue
                if match in seen:
                    continue
                seen.add(match)
                cleaned_match = html.unescape(match.rstrip("\n"))
                # Remove CDATA tags, which are here now
                cdata_match = re.match(CDATA_REGEX, cleaned_match)
                if cdata_match != None:
                    cleaned_match = cdata_match.groups(1)[0]
                # This might make the string empty again, so check for that
                if cleaned_match == "":
                    continue
                # Remove secondary issue tagging
                if cleaned_match[-1] == "^":
                    cleaned_match = cleaned_match[0:-1]

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

                # Approximation from the OpenAI website
                total_tokens += len(cleaned_match + "####") / 4

            print(f"Titles written. Estimated {total_tokens} tokens of training data.")
