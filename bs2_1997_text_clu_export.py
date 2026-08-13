"""Broken Sword II (1997) TEXT.CLU export tool / FEARka."""

import re
import struct
from pathlib import Path


SOURCE_ENCODING = "cp1252"  # The original TEXT.CLU is a one-byte, non-UTF-8 file.


def read_rows(path: Path):
    data = path.read_bytes()
    index_offset = struct.unpack_from("<I", data, 0)[0]
    if not 8 < index_offset <= len(data) or (len(data) - index_offset) % 8:
        raise ValueError("Invalid or unsupported TEXT.CLU file.")

    rows = []
    for table in range((len(data) - index_offset) // 8):
        offset, size = struct.unpack_from("<II", data, index_offset + table * 8)
        block = data[offset : offset + size]
        if len(block) < 0x30:
            raise ValueError(f"Invalid Text Resource table: {table}")
        name = block[10:36].split(b"\0", 1)[0].decode("ascii", "replace")
        match = re.search(r"Text Resource\s+(\d+)", name)
        if not match:
            raise ValueError(f"Unknown resource: {name}")
        resource = int(match.group(1))
        count = struct.unpack_from("<I", block, 0x2C)[0]
        if 0x30 + count * 4 > len(block):
            raise ValueError(f"Invalid pointer table: Text Resource {resource}")
        for row in range(count):
            pointer = struct.unpack_from("<I", block, 0x30 + row * 4)[0]
            if pointer == 0:
                rows.append((table, resource, row, None, "[EMPTY]"))
                continue
            end = block.find(b"\0", pointer + 2)
            if end < 0:
                raise ValueError(f"Unterminated string: table {table}, row {row}")
            text_id = struct.unpack_from("<H", block, pointer)[0]
            rows.append((table, resource, row, text_id, block[pointer + 2 : end].decode(SOURCE_ENCODING)))
    return rows


def make_id(table, resource, row, text_id):
    suffix = "EMPTY" if text_id is None else f"ID{text_id:04X}"
    return f"T{table:03d}_RES{resource}_R{row:04d}_{suffix}"


def tsv_text(text: str) -> str:
    start = len(text) - len(text.lstrip(" "))
    body = text[start:]
    end = len(body) - len(body.rstrip(" "))
    if end:
        body = body[:-end]
    body = body.replace("\t", "<tab>").replace("\r", "<cr>").replace("\n", "<lf>")
    return "[spc]" * start + body.replace('"', "¤") + "[spc]" * end


def po_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def main():
    print("Broken Sword II - The Smoking Mirror (1997) TEXT.CLU export / FEARka")
    print("\n1 - TEXT.tsv (id, original, translated)")
    print("2 - TEXT.po (for translation tools)")
    choice = input("Choose [1]: ").strip() or "1"
    if choice not in ("1", "2"):
        raise ValueError("Please choose 1 or 2.")
    rows = read_rows(Path("TEXT.CLU"))
    output = Path("TEXT.tsv" if choice == "1" else "TEXT.po")
    with output.open("w", encoding="utf-8", newline="\n") as out:
        if choice == "1":
            out.write("id\toriginal\ttranslated\n")
            for table, resource, row, text_id, text in rows:
                out.write(f"{make_id(table, resource, row, text_id)}\t{tsv_text(text)}\t\n")
        else:
            for table, resource, row, text_id, text in rows:
                out.write(f'msgctxt "{make_id(table, resource, row, text_id)}"\n')
                out.write(f'msgid "{po_text(text)}"\nmsgstr ""\n\n')
    print(f"\nExport complete: {output} ({len(rows)} rows)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError, struct.error) as error:
        print(f"\nERROR: {error}")
    finally:
        input("\nPress Enter to exit...")
