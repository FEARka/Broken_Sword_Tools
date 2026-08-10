import struct
import sys
from pathlib import Path

def import_txt_to_clu():
    print("--- Broken Sword 2 Remastered (3.3.0+) .clu import tool - FEARka ---")

    script_path = Path(sys.argv[0]).parent

    # Keresés, majd a _NEW.clu fájlok kiszűrése
    all_clu_files = list(script_path.glob("Text_*.clu"))
    clu_files = [f for f in all_clu_files if not f.name.endswith("_NEW.clu")]

    if not clu_files:
        print(f"Error: No source 'Text_*.clu' files found to use as a base.")
        return
    
    if len(clu_files) == 1:
        clu_path = clu_files[0]
        print(f"Found one base file, auto-selecting: {clu_path.name}")
    else:
        print("Multiple base .clu files found. Please choose one:")
        for i, file in enumerate(clu_files):
            print(f"  {i+1}: {file.name}")
        
        choice = -1
        while choice < 1 or choice > len(clu_files):
            try:
                choice = int(input(f"Enter a number (1-{len(clu_files)}): "))
            except ValueError:
                choice = -1
        clu_path = clu_files[choice - 1]

    txt_path = clu_path.with_name(f"{clu_path.stem}_translated.txt")
    output_path = clu_path.with_name(f"{clu_path.stem}_NEW.clu")

    # Javított hibakezelés
    if not txt_path.exists():
        print(f"Error: Input file for import not found.")
        print(f"Expected file at: '{txt_path}'")
        return

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            all_strings = [line for line in f.read().splitlines() if not line.startswith("--- TABLE") and line.strip()]
        with open(clu_path, 'rb') as f:
            original_data = f.read()
    except IOError as e:
        print(f"Error reading files: {e}")
        return

    print(f"Processing: {clu_path.name} -> {output_path.name}")
    print(f"Strings read from .txt file: {len(all_strings)}")

    main_table_offset = struct.unpack_from('<I', original_data, 0)[0]
    original_first_block_offset = struct.unpack_from('<I', original_data, main_table_offset)[0]

    final_data = bytearray(b'\x00\x00\x00\x00')
    static_header_block = original_data[4:original_first_block_offset]
    final_data.extend(static_header_block)

    new_resource_blocks = []
    unpadded_sizes = []
    string_index = 0
    
    original_table_entry_count = (len(original_data) - main_table_offset) // 8
    for entry_index in range(original_table_entry_count):
        current_main_offset = main_table_offset + (entry_index * 8)
        resource_offset, _ = struct.unpack_from('<II', original_data, current_main_offset)
        
        if resource_offset + 36 > len(original_data): break
        num_strings = struct.unpack_from('<I', original_data, resource_offset + 32)[0]
        
        header_and_pointers_size = 36 + num_strings * 4
        new_header = bytearray(header_and_pointers_size)
        new_header[0:36] = original_data[resource_offset : resource_offset + 36]

        string_data_part = bytearray()
        offsets_for_header = []
        gap_data = b''
        current_word_offset = 0

        if num_strings > 0:
            original_first_string_offset_in_words = struct.unpack_from('<I', original_data, resource_offset + 36)[0]
            gap_start_offset = resource_offset + header_and_pointers_size
            text_start_offset = resource_offset + (original_first_string_offset_in_words * 2)
            gap_data = original_data[gap_start_offset:text_start_offset]
            current_word_offset = original_first_string_offset_in_words

        for i in range(num_strings):
            if string_index >= len(all_strings):
                print("Error: The .txt file contains fewer lines than the original .clu file.")
                return
            offsets_for_header.append(current_word_offset)
            text_string = all_strings[string_index]
            binary_string = (text_string + '\x00').encode('utf-16-le')
            string_data_part.extend(binary_string)
            current_word_offset += len(binary_string) // 2
            string_index += 1

        for i, offset_val in enumerate(offsets_for_header):
            struct.pack_into('<I', new_header, 36 + i * 4, offset_val)
        
        new_block = bytes(new_header) + gap_data + bytes(string_data_part)
        unpadded_sizes.append(len(new_block))
        padding_needed = (4 - len(new_block) % 4) % 4
        new_block += b'\x00' * padding_needed
        new_resource_blocks.append(new_block)

    block_pointer_entries = bytearray()
    for i, block in enumerate(new_resource_blocks):
        current_block_offset = len(final_data)
        block_size = unpadded_sizes[i]
        block_pointer_entries.extend(struct.pack('<II', current_block_offset, block_size))
        final_data.extend(block)
    
    total_content_size = len(final_data)
    final_data.extend(struct.pack('<I', total_content_size))
    new_main_table_offset = len(final_data)
    final_data.extend(block_pointer_entries)
    struct.pack_into('<I', final_data, 0, new_main_table_offset)

    try:
        with open(output_path, 'wb') as f:
            f.write(final_data)
        print(f"Import successful! File saved to: {output_path.name}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    try:
        import_txt_to_clu()
        print("Done.")
    finally:
        input("Press Enter to exit...")