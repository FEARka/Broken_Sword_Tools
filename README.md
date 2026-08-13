# Broken Sword Tools
 
## Broken Sword - Shadow of the Templars (1996)
* bs1_1996_clu_export.py
* bs1_1996_clu_import_and_patch.py

**Required:**
* Python 3.10 or newer. When installing, make sure to check “Add python.exe to PATH.”

**Usage:**
* Copy the **swordres.rif** and **text.clu** files into the same folder as the .py files.
* Run **bs1_1996_clu_export.py**: this will extract the texts into **Text_exported.txt**.
* Translate it, then rename the finished file to **Text_translated.txt**.
* Run **bs1_1996_clu_import_and_patch.py**: this will insert the translated texts back into **text.clu** and modify **swordres.rif**.
* The new files will be created with the **_new** suffix.
----
## Broken Sword 2 - the Smoking Mirror (1997)
* bs2_1997_text_clu_export.py
* bs2_1997_text_clu_import.py

**Required:**
* Python 3.10 or newer. When installing, make sure to check “Add python.exe to PATH.”

**Usage:**
* Copy the **Text.clu** file into the same folder as the .py files.
* Run **bs2_1997_text_clu_export.py**: Choose format (tsv | po), and this will extract the texts into **Text.tsv|po**.
* Translate it. (TSV: Put the translation in the `translated` column. | PO: translation into `msgstr`.)
* Run **bs2_1997_text_clu_import.py**: Choose format (tsv | po), and this will insert the translated texts back into **Text.clu**.
* The new file will be created with the **_NEW** suffix.
----
## Broken Sword 2 - the Smoking Mirror: Remastered (2010)
* bs2_remastered_clu_export.py
* bs2_remastered_clu_import.py

**Required:**
* Python 3.10 or newer. When installing, make sure to check “Add python.exe to PATH.”

**Usage:**
* Copy the **text_*.clu** file into the same folder as the .py files.
* Run **bs2_remastered_clu_export.py**: this will extract the texts into **Text_*_exported.txt**.
* Translate it, then rename the finished file to **Text_*_translated.txt**.
* Run **bs2_remastered_clu_import.py**: this will insert the translated texts back into **Text_*.clu**.
* The new file will be created with the **_NEW** suffix.
