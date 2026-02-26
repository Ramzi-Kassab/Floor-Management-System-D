"""
Centralized variant case code constants.

These codes MUST match the seed_variant_cases management command.
Any new code added here must also be added to the seed command.

History:
  - OLD codes (deactivated by seed): NEW-ENO, USED-GRD, USED-STD, CLI-USED
  - CLAUDE.md previously documented old codes (NEW-CLI, USED-GRD, USED-CLI)
  - Corrected Feb 2026 to match actual seed data
"""


# ─── Active Variant Case Codes (from seed_variant_cases.py) ────────────────────

# NEW condition - ARDT owned
NEW_PUR = "NEW-PUR"       # New Purchased (from suppliers)
NEW_MFG = "NEW-MFG"       # New Manufactured (in-house)
NEW_RET = "NEW-RET"       # Retrofit (as New) — refurbished to new condition
NEW_EO = "NEW-EO"         # E&O (Excess & Obsolete) — new condition, discounted

# USED condition - ARDT owned
GRD_EO = "GRD-EO"         # E&O Ground — ground cutters in E&O stock
USED_RCL = "USED-RCL"     # Used Reclaimed (standard reclaim by ARDT)

# CLIENT owned
CLI_NEW = "CLI-NEW"        # Client New — new items provided by client
CLI_RCL = "CLI-RCL"        # Client Reclaimed — used/reclaimed from client


# ─── Grouped Constants ─────────────────────────────────────────────────────────

# All active variant case codes (order matches seed display_order)
ALL_VARIANT_CODES = [
    NEW_PUR, NEW_MFG, NEW_RET, NEW_EO,
    GRD_EO, USED_RCL,
    CLI_NEW, CLI_RCL,
]

# Codes considered "new" for stock calculations
NEW_VARIANT_CODES = {NEW_PUR, NEW_MFG, NEW_RET, NEW_EO}

# Codes considered "client" stock (ownership = CLIENT)
CLIENT_VARIANT_CODES = {CLI_NEW, CLI_RCL}


# ─── Display Codes for Cutter Inventory Dashboards ────────────────────────────
# These are the 7 columns shown in the cutter inventory dashboard / export.
# NEW-MFG is excluded because it's not used for PDC cutters.

CUTTER_DASHBOARD_CODES = [
    NEW_PUR, NEW_RET, NEW_EO,
    GRD_EO, USED_RCL,
    CLI_NEW, CLI_RCL,
]


# ─── Deprecated Code Aliases ──────────────────────────────────────────────────
# Some views and import commands still reference these old codes because
# existing database records may have been created with them.
# DO NOT use these for new code — they exist only for backward compatibility.

DEPRECATED_CODES = {
    "NEW-ENO": NEW_EO,      # Renamed to NEW-EO
    "USED-GRD": GRD_EO,     # Renamed to GRD-EO
    "USED-STD": USED_RCL,   # Renamed to USED-RCL
    "CLI-USED": CLI_RCL,    # Renamed to CLI-RCL
    "NEW-CLI": CLI_NEW,      # Old CLAUDE.md reference → CLI-NEW
    "USED-CLI": CLI_RCL,     # Old CLAUDE.md reference → CLI-RCL
}
