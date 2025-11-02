import struct
import os

def import_and_patch_dynamic(text_file="Text_translated.txt", original_clu_file="TEXT.CLU", output_clu_file="TEXT_new.CLU", rif_file="swordres.rif", output_rif_file="swordres_new.rif"):
    magic_marker = b'\x43\x68\x72\x54\x78\x74\x01\x00'
    input_text_encoding = 'utf-8-sig'
    output_binary_encoding = 'latin-1'
    NUM_ROWS_FIELD_OFFSET = 20
    POINTER_TABLE_START_OFFSET = 24
    
    try:
        print("Broken Sword - Shadow of the Templars (1996) .clu import tool / FEARka")
        print("--- IMPORT PROCESS STARTED ---")
        with open(text_file, 'r', encoding=input_text_encoding) as f:
            all_lines = f.readlines()

        tables_from_txt = []
        current_table_list = None
        for line in all_lines:
            stripped_line = line.rstrip('\n')
            if not stripped_line.strip(): continue
            if stripped_line.strip().startswith("--- TABLE"):
                current_table_list = []
                tables_from_txt.append(current_table_list)
            elif current_table_list is not None:
                current_table_list.append(stripped_line)

        with open(original_clu_file, 'rb') as f_orig, open(output_clu_file, 'wb') as f_new:
            original_data = f_orig.read()
            search_pos = 0
            new_file_pos = 0
            table_index = 0
            
            while True:
                table_start_pos = original_data.find(magic_marker, search_pos)
                if table_start_pos == -1 or table_start_pos >= 0x78C14: break
                num_rows_from_clu = struct.unpack_from('<I', original_data, table_start_pos + NUM_ROWS_FIELD_OFFSET)[0]
                if table_index >= len(tables_from_txt): break
                strings_for_this_table = tables_from_txt[table_index]
                if len(strings_for_this_table) != num_rows_from_clu:
                    print(f"CRITICAL ERROR: Row count mismatch in Table #{table_index}.")
                    return
                reconstructed_strings = ["" if s == "[EMPTY]" else s for s in strings_for_this_table]
                string_data_blob, new_pointer_table_bytes, current_string_offset_in_blob = bytearray(), bytearray(), 0
                header_size, pointer_table_size = POINTER_TABLE_START_OFFSET, num_rows_from_clu * 4
                text_block_start = header_size + pointer_table_size
                offset_base_in_table = NUM_ROWS_FIELD_OFFSET
                for s in reconstructed_strings:
                    if not s:
                        new_pointer_table_bytes.extend(struct.pack('<I', 0))
                    else:
                        relative_offset = (text_block_start + current_string_offset_in_blob) - offset_base_in_table
                        new_pointer_table_bytes.extend(struct.pack('<I', relative_offset))
                        encoded_s = s.encode(output_binary_encoding, errors='replace') + b'\x00'
                        string_data_blob.extend(encoded_s)
                        current_string_offset_in_blob += len(encoded_s)
                new_table_size = text_block_start + len(string_data_blob)
                new_data_size = new_table_size - 20
                f_new.write(magic_marker)
                f_new.write(struct.pack('<I', new_table_size))
                f_new.write(b'NONE')
                f_new.write(struct.pack('<I', new_data_size))
                f_new.write(struct.pack('<I', num_rows_from_clu))
                f_new.write(new_pointer_table_bytes)
                f_new.write(string_data_blob)
                search_pos, new_file_pos, table_index = table_start_pos + 1, new_file_pos + new_table_size, table_index + 1
            if table_start_pos != -1:
                f_new.write(original_data[table_start_pos:])
        print("Import to TEXT_new.CLU finished.")

        print("\n--- COLLECTING FINAL OFFSETS FROM NEW CLU FILE ---")
        collected_offset_data = bytearray()
        with open(output_clu_file, 'rb') as f_new_clu:
            new_clu_data = f_new_clu.read()
            search_pos, final_table_count = 0, 0
            while True:
                table_start = new_clu_data.find(magic_marker, search_pos)
                if table_start == -1: break
                table_size = struct.unpack_from('<I', new_clu_data, table_start + 8)[0]
                collected_offset_data.extend(struct.pack('<II', table_start, table_size))
                final_table_count += 1
                search_pos = table_start + 1
        print(f"Collected data for {final_table_count} tables.")

        print("\n--- DYNAMIC RIF PATCHING PROCESS STARTED ---")
        with open(rif_file, 'rb') as f_rif:
            rif_data = bytearray(f_rif.read())

        text_anchor_pos = rif_data.find(b'text')
        if text_anchor_pos == -1:
            print("CRITICAL ERROR: Could not find 'text' anchor in RIF file.")
            return
        print(f"Found 'text' anchor at: {hex(text_anchor_pos)}")
        
        lang_count_pos = text_anchor_pos + 32
        
        lang_count = rif_data[lang_count_pos]
        print(f"Found language count: {lang_count}")

        base_address = 0xBB4
        base_lang_count = 5
        patch_start_address = base_address + (lang_count - base_lang_count) * 4
        print(f"Calculated patch start address: {hex(patch_start_address)}")

        chunk_size, skip_size = 544, 276
        source_pos, dest_pos = 0, patch_start_address
        
        while source_pos < len(collected_offset_data):
            chunk_to_write = collected_offset_data[source_pos : source_pos + chunk_size]
            rif_data[dest_pos : dest_pos + len(chunk_to_write)] = chunk_to_write
            source_pos += chunk_size
            dest_pos += chunk_size + skip_size
        
        with open(output_rif_file, 'wb') as f_out_rif:
            f_out_rif.write(rif_data)
        
        print(f"Patching {output_rif_file} finished.")

    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e.filename}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_and_patch_dynamic()
    input("\nFinished. Press Enter to exit...")