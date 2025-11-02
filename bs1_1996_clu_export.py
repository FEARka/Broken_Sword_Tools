import struct
import os

def export_text_clu_FINAL(input_file="TEXT.CLU", output_file="Text_exported.txt", end_offset=0x78C14):
    magic_marker = b'\x43\x68\x72\x54\x78\x74\x01\x00'
    NUM_ROWS_FIELD_OFFSET = 20
    POINTER_TABLE_START_OFFSET = 24
    
    try:
        print("Broken Sword - Shadow of the Templars (1996) .clu export tool / FEARka")
        print(f"Processing: {input_file}")
        
        with open(input_file, 'rb') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
            data = f_in.read(end_offset)
            search_pos = 0
            table_index = 0
            
            while True:
                table_start_pos = data.find(magic_marker, search_pos)
                if table_start_pos == -1: break

                if table_index > 0:
                    f_out.write("\n")

                num_rows = struct.unpack_from('<I', data, table_start_pos + NUM_ROWS_FIELD_OFFSET)[0]
                
                f_out.write(f"--- TABLE {table_index} (Rows: {num_rows}) ---\n")
                
                pointer_table_start = table_start_pos + POINTER_TABLE_START_OFFSET
                offset_base = table_start_pos + NUM_ROWS_FIELD_OFFSET
                
                for i in range(num_rows):
                    relative_offset = struct.unpack_from('<I', data, pointer_table_start + (i * 4))[0]
                    if relative_offset == 0:
                        f_out.write('[EMPTY]\n')
                    else:
                        string_pos = offset_base + relative_offset
                        string_end_pos = data.find(b'\x00', string_pos)
                        string_bytes = data[string_pos:string_end_pos]
                        decoded_string = string_bytes.decode('latin-1')
                        f_out.write(decoded_string + '\n')

                search_pos = table_start_pos + 1
                table_index += 1
        
        print(f"Export successful! File saved to: {output_file}")
        print("Done.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    export_text_clu_FINAL()
    input("\nPress Enter to exit...")