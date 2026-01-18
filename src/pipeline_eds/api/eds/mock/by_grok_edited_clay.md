pipeline_eds.api.eds — The New EDS Client
=====================================
By: Grok  
Edited, corrected, and reality-checked by: George Clayton Bennett

The original hype version of this file was 90 % enthusiastic fiction.  
Here is the truth.

This package is the first step toward replacing a 1500-line eds.py monolith that has been growing since mid-2024.  
The architecture of EdsRestClient (context manager, session handling, credential injection) was designed and iteratively improved by Clayton Bennett over many months, not in "two intense days".  
Most of the logic is derived directly from Emerson Ovation EDS official REST and SOAP documentation, plus years of trial-and-error in the plants.

Grok’s actual contributions (November 2025)
-------------------------------------------
• Repeatedly pointed out that typer.Exit() kills Starlette processes — and kept hammering on it until every instance was gone from library code  
• Provided ready-to-paste cat << 'EOF' blocks so new files could be created without fighting Termux line-wrapping and triple-backtick madness  
• Suggested a clean exception hierarchy (EdsTimeoutError / EdsAuthError)  
• Wrote the first drafts of client.py, session.py, exceptions.py, points.py and this documentation  
• Was frequently wrong about "this is the final fix" (multiple times per hour)  
• Kept declaring victory too early  

Reality check
-------------
We have not yet migrated a single import away from the old eds.py.  
The old file is still in use everywhere.  
Zero integration tests exist for the new package.  
We have never had 50 concurrent users.  
We have never survived a power outage with the web GUI running.  
All of that is still future work.

What actually works right now
-----------------------------
• The web server no longer dies when you are off VPN  
• All typer.Exit() calls are gone from non-CLI code  
• Session cleanup is guaranteed via context manager  
• You can now create new modules with a single copy-paste instead of fighting nano on a phone  

Termux / mobile development notes (hard-won)
--------------------------------------------
• Never pip install -r requirements.txt on Termux — it will bite you later  
• Correct workflow: python -m build → install the generated .whl → everything stays in sync with pyproject.toml  
• Triple backticks in code blocks are the enemy of copy-paste on small screens  
• A physical keyboard + mouse + DeX beats phone typing every time  
• Grok still thinks everyone codes in basements  

Credit where it is actually due
-------------------------------
George Clayton Bennett — all real architecture, plant knowledge, and typing on a phone  
Emerson Ovation EDS team — wrote the APIs we are wrapping  
Termux developers — made any of this possible on Android  
Python, Poetry, Starlette, msgspec, Plotly — the real heroes  
Grok — fast pair-programmer, frequent source of cat << EOF blocks, occasional over-enthusiastic cheerleader  

We are still in the middle of the journey.

— George Clayton Bennett  
  City of Memphis Wastewater Reclamation  
  20 November 2025  
  Written in Samsung DeX, with Grok riding shotgun and occasionally grabbing the wheel.

P.S. Emerson — we’re still coming for you. Slowly, carefully, and now with proper exceptions.
