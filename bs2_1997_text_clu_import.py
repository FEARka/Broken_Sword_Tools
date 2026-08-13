"""Broken Sword II (1997) TEXT.CLU import tool / FEARka."""

import ast
import re
import struct
from pathlib import Path


SOURCE_ENCODING = "cp1252"  # Encoding of the original English TEXT.CLU.
TARGET_ENCODING = "cp1252"  # Supports Spanish n-tilde; use o-circumflex/u-circumflex for Hungarian long vowels.
ID_RE = re.compile(r"^T(\d+)_RES(\d+)_R(\d+)_(?:ID([0-9A-Fa-f]{4})|EMPTY)$")


def make_id(table, resource, row, text_id):
    suffix = "EMPTY" if text_id is None else f"ID{text_id:04X}"
    return f"T{table:03d}_RES{resource}_R{row:04d}_{suffix}"


def read_clu(path: Path):
    data = path.read_bytes()
    index_offset = struct.unpack_from("<I", data, 0)[0]
    if not 8 < index_offset <= len(data) or (len(data) - index_offset) % 8:
        raise ValueError("Invalid or unsupported TEXT.CLU file.")
    tables, last_end = [], 8
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
        rows = []
        for row in range(count):
            pointer = struct.unpack_from("<I", block, 0x30 + row * 4)[0]
            if pointer == 0:
                rows.append((row, None, "[EMPTY]", b""))
                continue
            end = block.find(b"\0", pointer + 2)
            if end < 0:
                raise ValueError(f"Unterminated string: table {table}, row {row}")
            text_id = struct.unpack_from("<H", block, pointer)[0]
            raw = block[pointer + 2 : end]
            rows.append((row, text_id, raw.decode(SOURCE_ENCODING), raw))
        tables.append((table, resource, block[:0x30], rows))
        last_end = max(last_end, offset + size)
    return data[:8], data[last_end:index_offset], tables


def parse_id(value):
    match = ID_RE.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid ID: {value!r}")
    return match.groups()


def from_tsv_text(text: str) -> str:
    start = 0
    while text.startswith("[spc]"):
        start += 1
        text = text[5:]
    end = 0
    while text.endswith("[spc]"):
        end += 1
        text = text[:-5]
    text = text.replace("<tab>", "\t").replace("<cr>", "\r").replace("<lf>", "\n")
    return " " * start + text.replace("¤", '"') + " " * end


def read_tsv(path: Path):
    translated = {}
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        if source.readline().rstrip("\r\n") != "id\toriginal\ttranslated":
            raise ValueError("Invalid TSV header: expected id<TAB>original<TAB>translated.")
        for number, line in enumerate(source, 2):
            line = line.rstrip("\r\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                raise ValueError(f"TSV line {number} must contain exactly three columns.")
            key, _original, value = parts
            parse_id(key)
            if key in translated:
                raise ValueError(f"Duplicate ID in TSV: {key}")
            translated[key] = from_tsv_text(value) if value else ""
    return translated


def po_string(value, line):
    try:
        result = ast.literal_eval(value)
    except (SyntaxError, ValueError) as error:
        raise ValueError(f"Invalid PO quoting or escape on line {line}.") from error
    if not isinstance(result, str):
        raise ValueError(f"Invalid PO value on line {line}.")
    return result


def read_po(path: Path):
    translated, entry, active = {}, {}, None

    def finish(line):
        nonlocal entry, active
        if not entry:
            return
        if set(entry) == {"msgid", "msgstr"} and entry["msgid"] == "":
            entry, active = {}, None  # Standard PO metadata header.
            return
        if set(entry) != {"msgctxt", "msgid", "msgstr"}:
            raise ValueError(f"Incomplete PO entry near line {line}.")
        key = entry["msgctxt"]
        parse_id(key)
        if key in translated:
            raise ValueError(f"Duplicate ID in PO: {key}")
        translated[key] = entry["msgstr"]
        entry, active = {}, None

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        line_number = 0
        for line_number, line in enumerate(source, 1):
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                if not line:
                    finish(line_number)
                continue
            match = re.match(r'^(msgctxt|msgid|msgstr) (".*")$', line)
            if match:
                if match.group(1) == "msgctxt" and entry:
                    finish(line_number)
                active = match.group(1)
                entry[active] = po_string(match.group(2), line_number)
            elif line.startswith('"') and line.endswith('"') and active:
                entry[active] += po_string(line, line_number)
            else:
                raise ValueError(f"Invalid PO line {line_number}: {line!r}")
        finish(line_number)
    return translated


def build_clu(file_header, padding, tables, translations):
    expected = {make_id(table, resource, row, text_id) for table, resource, _, rows in tables for row, text_id, _, _ in rows}
    if set(translations) != expected:
        missing = expected - set(translations)
        extra = set(translations) - expected
        key = sorted(missing or extra)[0]
        raise ValueError(f"Missing or unknown ID: {key}")

    output, index = bytearray(file_header), bytearray()
    for table, resource, header, rows in tables:
        pointers, strings = bytearray(), bytearray()
        for row, text_id, original, original_bytes in rows:
            key = make_id(table, resource, row, text_id)
            value = translations[key]
            if text_id is None:
                if value not in ("", "[EMPTY]"):
                    raise ValueError(f"Cannot add text to an [EMPTY] entry: {key}")
                pointers.extend(struct.pack("<I", 0))
                continue
            try:
                encoded = original_bytes if value == "" else value.encode(TARGET_ENCODING)
            except UnicodeEncodeError as error:
                raise ValueError(
                    f"This character cannot be encoded with {TARGET_ENCODING} "
                    f"in {key}: {error}"
                ) from error
            pointers.extend(struct.pack("<I", 0x30 + len(rows) * 4 + len(strings)))
            strings.extend(struct.pack("<H", text_id) + encoded + b"\0")
        block = header + pointers + strings
        index.extend(struct.pack("<II", len(output), len(block)))
        output.extend(block)
    output.extend(padding)
    struct.pack_into("<I", output, 0, len(output))
    output.extend(index)
    return output


def main():
    print("Broken Sword II - The Smoking Mirror (1997) TEXT.CLU import / FEARka")
    print("\n1 - TEXT.tsv")
    print("2 - TEXT.po")
    choice = input("Choose [1]: ").strip() or "1"
    if choice not in ("1", "2"):
        raise ValueError("Please choose 1 or 2.")
    print("Using cp1252 game encoding (use o-circumflex / u-circumflex for Hungarian long vowels)")
    translation_file = Path("TEXT.tsv" if choice == "1" else "TEXT.po")
    if not Path("TEXT.CLU").is_file():
        raise FileNotFoundError("TEXT.CLU was not found in this folder.")
    if not translation_file.is_file():
        raise FileNotFoundError(f"Translation file was not found: {translation_file}")
    translations = read_tsv(translation_file) if choice == "1" else read_po(translation_file)
    header, padding, tables = read_clu(Path("TEXT.CLU"))
    Path("TEXT_NEW.CLU").write_bytes(build_clu(header, padding, tables, translations))
    print(f"\nImport complete: TEXT_NEW.CLU ({len(tables)} Text Resource tables)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, UnicodeError, ValueError, struct.error) as error:
        print(f"\nERROR: {error}")
    finally:
        input("\nPress Enter to exit...")
