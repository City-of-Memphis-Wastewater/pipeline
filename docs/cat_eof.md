Using cat << 'EOF' with AI on a phone — the real way
===================================================

This is the only workflow that actually works 100 % of the time when you have:
• Termux / Samsung DeX / SSH on a phone
• No mouse, no VS Code, no reliable clipboard
• A text-only AI (Grok, Claude, etc.)

The method: cat << 'EOF' (or 'EOM') + one file per paste

Why it works
------------
• No triple backticks → nothing gets eaten by Markdown
• Single-quoted delimiter → zero shell expansion, dollars and backticks survive
• Exact byte-for-byte copy → what the AI wrote is what lands on disk
• Works even when your terminal only has 5000-line scrollback


Hard limits you will hit every single time
------------------------------------------
1. AI context window (8k–32k tokens) → never ask for 10 files at once
2. Android/Termux scrollback → usually less than 16 000 lines → giant paste silently disappears
3. Line-length limits → some keyboards/SSH clients die above 4000 chars per line

Golden rule
-----------
One file per paste. Always.

Do this:
cat << 'EOF' > src/pipeline/api/eds/client.py
# whole file


Hard limits you will hit every single time
------------------------------------------
1. AI context window (8k–32k tokens) → never ask for 10 files at once
2. Android/Termux scrollback → usually less than 16 000 lines → giant paste silently disappears
3. Line-length limits → some keyboards/SSH clients die above 4000 chars per line

Golden rule
-----------
One file per paste. Always.

Do this:
cat << 'EOF' > src/pipeline/api/eds/client.py
# whole file


Hard limits you will hit every single time
------------------------------------------
1. AI context window (8k–32k tokens) → never ask for 10 files at once
2. Android/Termux scrollback → usually less than 16 000 lines → giant paste silently disappears
3. Line-length limits → some keyboards/SSH clients die above 4000 chars per line

Golden rule
-----------
One file per paste. Always.

Do this:
cat << 'EOF' > src/pipeline/api/eds/client.py
# whole file


Editing existing files — phone-safe methods
-------------------------------------------
Never trust a diff or sed one-liner on a 5-inch screen.

Method 1 — full replacement (safest)
cp file.py file.py.bak
cat << 'EOF' > file.py
# complete new version from AI


Checklist before you hit Enter
------------------------------
- Delimiter (EOF/EOM/DONE) appears nowhere inside the code
- You used single quotes: << 'EOF'
- Path is correct (tab-complete it)
- You have a backup if overwriting
- You are doing exactly one file

You will mess it up sometimes.  
When you do: cp file.py.bak file.py and try again.

This method is ugly, primitive, and 100 % reliable.
It is why I can refactor production code on a phone in the field.

— George Clayton Bennett  
  City of Memphis Wastewater  
  20 November 2025  
  Still using cat << 'EOF' and still winning.
