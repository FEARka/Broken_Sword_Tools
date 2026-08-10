import struct
import sys
from pathlib import Path

def export_clu_to_txt():
    print("--- Broken Sword 2 Remastered (3.3.0+) .clu export tool - FEARka ---")
    
    script_path = Path(sys.argv[0]).parent
    
    # Keresés, majd a _NEW.clu fájlok kiszűrése
    all_clu_files = list(script_path.glob("Text_*.clu"))
    clu_files = [f for f in all_clu_files if not f.name.endswith("_NEW.clu")]

    if not clu_files:
        print(f"Error: No source 'Text_*.clu' files found to export.")
        return
    
    if len(clu_files) == 1:
        clu_path = clu_files[0]
        print(f"Found one file, auto-selecting: {clu_path.name}")
    else:
        print("Multiple .clu files found. Please choose one:")
        for i, file in enumerate(clu_files):
            print(f"  {i+1}: {file.name}")
        
        choice = -1
        while choice < 1 or choice > len(clu_files):
            try:
                choice = int(input(f"Enter a number (1-{len(clu_files)}): "))
            except ValueError:
                choice = -1
        clu_path = clu_files[choice - 1]

    txt_path = clu_path.with_name(f"{clu_path.stem}_exported.txt")

    print(f"Processing: {clu_path.name}")

    try:
        with open(clu_path, 'rb') as f:
            data = f.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        return

    main_table_offset = struct.unpack_from('<I', data, 0)[0]
    output_lines = []
    table_counter = 0
    
    original_table_entry_count = (len(data) - main_table_offset) // 8
    for entry_index in range(original_table_entry_count):
        current_main_offset = main_table_offset + (entry_index * 8)
        
        try:
            resource_offset, resource_size = struct.unpack_from('<II', data, current_main_offset)
        except struct.error:
            print(f"Warning: Could not read table pointer at offset {current_main_offset}.")
            break
        
        table_counter += 1
        if table_counter > 1:
            output_lines.append("")

        num_strings = struct.unpack_from('<I', data, resource_offset + 32)[0]
        output_lines.append(f"--- TABLE {table_counter} (Rows: {num_strings}) ---")
        
        sub_table_start = resource_offset + 36
        offsets = [struct.unpack_from('<I', data, sub_table_start + i * 4)[0] for i in range(num_strings)]

        for i in range(num_strings):
            start_word_offset = offsets[i]
            start_byte_offset = resource_offset + (start_word_offset * 2)
            end_byte_offset = resource_offset + (offsets[i + 1] * 2) if i + 1 < num_strings else resource_offset + resource_size
            string_data = data[start_byte_offset:end_byte_offset]
            
            try:
                decoded_string = string_data.decode('utf-16-le').rstrip('\x00')
                output_lines.append(decoded_string)
            except UnicodeDecodeError:
                output_lines.append("[DECODING_ERROR]")

    try:
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        print(f"Export successful! File saved to: {txt_path.name}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    try:
        export_clu_to_txt()
        print("Done.")
    finally:
        input("Press Enter to exit...")