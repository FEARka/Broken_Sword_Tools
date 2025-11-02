# Broken Sword Tools
## Broken Sword - Shadow of the Templar (1996)
* bs1_1996_clu_export.py
* bs1_1996_clu_import_and_patch.py

**Required:**
* Python. When installing, make sure to check “Add python.exe to PATH.”

**Usage:**
* Copy the **swordres.rif** and **text.clu** files into the same folder as the .py files.
* Run **bs1_1996_clu_export.py**: this will extract the texts into **Text_exported.txt**.
* Translate it, then rename the finished file to **Text_translated.txt**.
* Run **bs1_1996_clu_import_and_patch.py**: this will insert the translated texts back into **text.clu** and modify **swordres.rif**.
* The new files will be created with the **_new** suffix.
