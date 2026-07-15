"""
generate_synthetic_data.py
Generates BPCL Mathura Refinery synthetic data:
  - pump_manual.pdf (realistic O&M manual)
  - SOP_P201_Maintenance_v2019.pdf (old — 80Nm, LOTO A then B)
  - SOP_P201_Maintenance_v2024.pdf (new — 95Nm, LOTO B then A — CONTRADICTS 2019)
  - SOP_Compressor_C101_SafetyProcedure.pdf (OISD-105 compliant)
  - work_orders_bpcl.csv (20 SAP PM work orders)
  - rca_reports_bpcl.json (5 RCA reports)
"""
import os
import json
import csv
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not found. Install with: pip install pymupdf")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLE_DIR = os.path.join(BASE_DIR, "backend", "data", "sample")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def make_pdf(path: str, title: str, sections: list[tuple[str, str]]):
    """Create a PDF with a title and list of (heading, body) sections."""
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    y = 60
    # Title
    page.insert_text((50, y), title, fontname="helv", fontsize=16, color=(0.1, 0.2, 0.5))
    y += 30
    page.insert_text((50, y), "BPCL Mathura Refinery — Rotating Equipment Division", fontsize=10, color=(0.4, 0.4, 0.4))
    y += 25
    page.draw_line((50, y), (545, y), color=(0.3, 0.3, 0.3), width=0.5)
    y += 20

    for heading, body in sections:
        if y > 780:
            page = doc.new_page(width=595, height=842)
            y = 60

        page.insert_text((50, y), heading, fontname="helv", fontsize=12,
                         color=(0.1, 0.3, 0.6))
        y += 18

        # Word-wrap body text
        words = body.split()
        line, lines = [], []
        for w in words:
            line.append(w)
            if len(" ".join(line)) > 85:
                lines.append(" ".join(line[:-1]))
                line = [w]
        if line:
            lines.append(" ".join(line))

        for ln in lines:
            if y > 800:
                page = doc.new_page(width=595, height=842)
                y = 60
            page.insert_text((55, y), ln, fontsize=9, color=(0.1, 0.1, 0.1))
            y += 14
        y += 10

    doc.save(path)
    doc.close()
    print(f"✅ Created {path}")


# ── 1. PUMP MANUAL ────────────────────────────────────────────────────────────
make_pdf(
    os.path.join(SAMPLE_DIR, "pump_manual.pdf"),
    "P-201 Crude Oil Transfer Pump — Operation & Maintenance Manual",
    [
        ("1. Equipment Description",
         "Asset Tag: P-201. Type: Horizontal Single-Stage Centrifugal Pump. "
         "Service: Crude Oil Transfer from Tank Farm TK-101 to CDU Feed. "
         "Manufacturer: Flowserve Corporation. Model: PVXM 200. Year: 2018. "
         "Plant: BPCL Mathura Refinery, Unit 2 — Crude Distillation Unit (CDU)."),

        ("2. Design Parameters",
         "Rated Flow: 850 m3/hr. Rated Head: 145 m. Speed: 1480 RPM. "
         "Motor Power: 450 kW. Operating Temperature: 40 degC. "
         "Suction Pressure: 0.3 bar g. Discharge Pressure: 15.2 bar g. "
         "Specific Gravity: 0.85. Viscosity: 12 cSt. NPSH Required: 4.2 m."),

        ("3. Bearing Specifications",
         "Drive End Bearing: SKF 6316 (Deep Groove Ball Bearing). "
         "Non-Drive End Bearing: SKF NU316 (Cylindrical Roller Bearing). "
         "Bearing Inner Race Fault Frequency (BPFI): 103.4 Hz at 1480 RPM. "
         "Bearing Outer Race Fault Frequency (BPFO): 68.2 Hz at 1480 RPM. "
         "Ball Pass Frequency (BSF): 45.1 Hz. Cage Frequency: 8.9 Hz. "
         "Lubrication: Mobil SHC 100 grease. Regreasing interval: 1000 hours."),

        ("4. Vibration Acceptance Criteria",
         "Per ISO 10816-3 and API 610 12th Edition: "
         "Zone A (New machine acceptable): 0 to 2.8 mm/s RMS. "
         "Zone B (Long-term operation acceptable): 2.8 to 7.1 mm/s RMS. "
         "Zone C (Alarm threshold — restricted operation): 7.1 to 11.2 mm/s RMS. "
         "Zone D (Danger — immediate shutdown required): greater than 11.2 mm/s RMS. "
         "High vibration alarm setpoint: 7.1 mm/s. Shutdown setpoint: 11.2 mm/s."),

        ("5. Mechanical Seal",
         "Type: John Crane Type 2800 Double Mechanical Seal. "
         "Seal Flush Plan: API Plan 53B (pressurized barrier fluid). "
         "Barrier Fluid Pressure: 1.5 bar above seal chamber pressure. "
         "Barrier Fluid: Shell Tellus S2 M 46 (hydraulic oil). "
         "Seal flush flow rate: 2–3 LPM. Maximum seal temperature: 80 degC."),

        ("6. Bearing Replacement Interval",
         "Replace bearings every 8,000 operating hours OR when vibration "
         "exceeds 7.1 mm/s RMS (Zone C threshold), whichever occurs first. "
         "Condition-based replacement recommended if bearing temperature "
         "exceeds 85 degC or if envelope spectrum shows BPFI/BPFO peaks "
         "greater than 3x running speed amplitude."),

        ("7. LOTO (Lockout-Tagout) Procedure",
         "STEP 1: Notify Control Room operator and obtain Permit to Work (PTW). "
         "STEP 2: Close suction isolation valve V-201A (handwheel, 5 turns CW). "
         "STEP 3: Close discharge isolation valve V-201B (handwheel, 8 turns CW). "
         "STEP 4: De-energize MCC-2 breaker CB-201 (Lock with personal padlock). "
         "STEP 5: Tag out at both valve handwheels and MCC breaker. "
         "STEP 6: Open vent valve V-201C to depressurize casing. "
         "STEP 7: Verify zero energy state with calibrated pressure gauge."),

        ("8. Maintenance Schedule",
         "Daily: Check bearing temperature (max 85 degC), seal flush pressure (1.5 bar), "
         "vibration level (max 7.1 mm/s). Monthly: Grease bearing housings (15g each). "
         "Quarterly: Check coupling alignment (max 0.05 mm offset, 0.03 mm angular). "
         "Annually: Inspect mechanical seal, replace O-rings and wear rings. "
         "8000 hours: Complete bearing replacement, clearance check, impeller inspection."),

        ("9. Common Fault Signatures",
         "CAVITATION: Crackling noise, high vibration at vane pass frequency (VPF = 5x RPM). "
         "Check NPSH margin. Throttle discharge slightly. "
         "BEARING WEAR: High vibration at BPFI (103 Hz) or BPFO (68 Hz). Plan bearing change. "
         "MISALIGNMENT: High vibration at 2x RPM (49.3 Hz). Check coupling. "
         "IMBALANCE: High vibration at 1x RPM (24.7 Hz). Balance impeller. "
         "SEAL FAILURE: Barrier fluid level drop more than 10% in 24 hours. Emergency shutdown."),

        ("10. Spare Parts List",
         "SKF 6316 Bearing (Drive End): BPCL SAP Material No. 10045612. "
         "SKF NU316 Bearing (NDE): BPCL SAP Material No. 10045613. "
         "John Crane 2800 Seal Kit: BPCL SAP Material No. 20087234. "
         "Coupling Insert (Falk Steelflex T10): BPCL SAP Material No. 30012456. "
         "Impeller Wear Ring Set: BPCL SAP Material No. 10098765. "
         "Minimum stock: 2 complete bearing sets always on hand (critical rotating equipment).")
    ]
)

# ── 2. SOP 2019 (old — 80Nm, LOTO A then B) ──────────────────────────────────
make_pdf(
    os.path.join(SAMPLE_DIR, "SOP_P201_Maintenance_v2019.pdf"),
    "SOP-P201-MAINT-001 Rev.2 — P-201 Pump Maintenance Procedure (2019)",
    [
        ("Document Control",
         "Revision: 2. Date: 15-Mar-2019. Author: S.K. Sharma (Sr. Mechanical Engineer). "
         "Approved by: V.P. Mishra (Head, Maintenance). "
         "Next Review Due: March 2022. Status: SUPERSEDED — DO NOT USE."),

        ("1. Scope",
         "This procedure covers planned maintenance activities for P-201 Crude Oil "
         "Transfer Pump including bearing replacement, coupling inspection, and "
         "mechanical seal servicing at BPCL Mathura Refinery Unit 2."),

        ("2. Torque Specifications",
         "WARNING: All bolts must be torqued to specification using calibrated torque wrench. "
         "Coupling bolts (M24 grade 8.8): TORQUE TO 80 Nm (as per Flowserve OEM manual 2015 edition). "
         "Bearing housing end cover bolts (M16): 45 Nm. "
         "Baseplate hold-down bolts (M30): 180 Nm. "
         "Casing flange bolts (M20): 95 Nm."),

        ("3. LOTO Sequence (2019 Version)",
         "LOTO STEP A: First close SUCTION valve V-201A completely (handwheel, 5 turns CW). "
         "LOTO STEP B: Then close DISCHARGE valve V-201B completely (handwheel, 8 turns CW). "
         "LOTO STEP C: De-energize MCC-2 breaker CB-201 and lock with personal padlock. "
         "NOTE: Sequence A then B is critical — do not reverse. "
         "LOTO STEP D: Attach danger tags at V-201A handwheel, V-201B handwheel, and MCC-2. "
         "LOTO STEP E: Open vent valve V-201C to release casing pressure."),

        ("4. PPE Requirements",
         "Chemical resistant gloves (nitrile, minimum 6mil thickness). "
         "Safety glasses or face shield. Steel-toed safety boots. "
         "Flame-resistant coveralls (Category 2). "
         "Hard hat. Hearing protection when pump is running."),

        ("5. Bearing Replacement",
         "Use bearing puller to remove old bearings. Do not use heat gun unless bearings "
         "are seized (heat to maximum 100 degC using induction heater only — no open flame). "
         "Clean bearing housing with lint-free cloth and isopropyl alcohol. "
         "Press new bearing using hydraulic press or freeze fit (liquid nitrogen, -40 degC). "
         "Apply Mobil SHC 100 grease (15g per housing) after installation.")
    ]
)

# ── 3. SOP 2024 (new — 95Nm, LOTO B then A — CONTRADICTS 2019) ───────────────
make_pdf(
    os.path.join(SAMPLE_DIR, "SOP_P201_Maintenance_v2024.pdf"),
    "SOP-P201-MAINT-001 Rev.5 — P-201 Pump Maintenance Procedure (2024)",
    [
        ("Document Control",
         "Revision: 5. Date: 10-Jan-2024. Author: R. Gupta (Lead Mechanical Engineer). "
         "Approved by: A.K. Singh (Head, Reliability Engineering). "
         "Supersedes: Rev.2 dated March 2019. Status: ACTIVE — CURRENT APPROVED VERSION."),

        ("1. Scope",
         "This procedure covers planned maintenance for P-201 Crude Oil Transfer Pump. "
         "Updated per API 610-12th Edition (2021) and BPCL Engineering Standard BES-ME-007 Rev.3. "
         "All previous revisions (Rev.1 through Rev.4) are superseded and must be destroyed."),

        ("2. Torque Specifications — REVISED",
         "IMPORTANT: Torque values updated per API 610-12th Edition (2021) — "
         "OEM Flowserve issued Service Bulletin SB-PVXM-2023-04 revising coupling bolt torque. "
         "Coupling bolts (M24 grade 8.8): TORQUE TO 95 Nm (REVISED from 80 Nm in Rev.2). "
         "Bearing housing end cover bolts (M16): 45 Nm (unchanged). "
         "Baseplate hold-down bolts (M30): 180 Nm (unchanged). "
         "Casing flange bolts (M20): 95 Nm (unchanged)."),

        ("3. LOTO Sequence — REVISED per OISD-105 Section 6.4",
         "SAFETY CRITICAL: LOTO sequence revised per OISD-105 (2022 revision) Section 6.4 "
         "and incident investigation report IIR-BPCL-MTR-2022-019. "
         "LOTO STEP B: First close DISCHARGE valve V-201B completely (handwheel, 8 turns CW). "
         "LOTO STEP A: Then close SUCTION valve V-201A completely (handwheel, 5 turns CW). "
         "NOTE: Sequence B then A is now mandatory — reverse of previous Rev.2. "
         "Closing discharge first prevents reverse flow and cavitation during isolation. "
         "LOTO STEP C: De-energize MCC-2 breaker CB-201 and lock with personal padlock. "
         "LOTO STEP D: Attach danger tags at V-201B handwheel, V-201A handwheel, and MCC-2. "
         "LOTO STEP E: Open vent valve V-201C to release casing pressure. "
         "LOTO STEP F: Test for zero energy — verify 0 bar on pressure gauge PI-201."),

        ("4. PPE Requirements",
         "Chemical resistant gloves (nitrile, minimum 8mil thickness — upgraded from 6mil). "
         "Full face shield (not safety glasses alone for crude oil service). "
         "Steel-toed safety boots with chemical resistant sole. "
         "Flame-resistant coveralls (Category 2 minimum, Cat 3 preferred). "
         "Hard hat. Hearing protection. "
         "H2S monitor mandatory — crude service may contain up to 50 ppm H2S."),

        ("5. Bearing Replacement — Updated",
         "Use SKF TMHP 10 bearing puller or equivalent. Do not impact bearings. "
         "Clean housing with approved solvent (Exxon Varsol 60 or equivalent). "
         "Install bearing using SKF THAP 200 hydraulic fit method. "
         "Grease quantity increased: Apply Mobil SHC 100 grease (20g per housing) — "
         "increased from 15g per Flowserve Service Bulletin SB-PVXM-2023-04. "
         "Document bearing serial number in SAP PM notification.")
    ]
)

# ── 4. COMPRESSOR SOP (OISD-105 compliant) ───────────────────────────────────
make_pdf(
    os.path.join(SAMPLE_DIR, "SOP_Compressor_C101_SafetyProcedure.pdf"),
    "SOP-C101-SAFE-003 — C-101 Reciprocating Compressor Safety & Maintenance",
    [
        ("Document Control",
         "Asset: C-101 — Natural Gas Reciprocating Compressor. "
         "Revision: 4. Date: 22-Sep-2023. Plant: BPCL Mathura Refinery, Unit 3 — Gas Recovery. "
         "Compliant with: OISD-105, OISD-117, OSHA 1910.147, API 618."),

        ("1. LOTO (Lockout-Tagout) Procedure — OISD-105 Compliant",
         "MANDATORY per OISD-105 Section 5.3 and OSHA 1910.147. "
         "Step 1: Obtain Permit to Work (PTW) No. from Area Operations Supervisor. "
         "Step 2: Notify all personnel in compressor bay. "
         "Step 3: Shutdown compressor via DCS — wait for coast-down (3 minutes minimum). "
         "Step 4: Close inlet gas valve XV-101A and outlet valve XV-101B — lockout with padlock. "
         "Step 5: De-energize MCC-3 breaker CB-301 — lockout with personal padlock. "
         "Step 6: Tagout all isolation points with Danger Tags. "
         "Step 7: Vent and purge with nitrogen — 3 purge cycles minimum. "
         "Step 8: Gas test — verify 0% LEL before entry. Document in PTW."),

        ("2. Electrostatic Grounding",
         "Per OISD-GDN-180 and OISD-117 Section 7.2: "
         "All portable equipment, hoses, and containers must be bonded and grounded "
         "before any work involving flammable gas or liquids. "
         "Connect grounding cable to designated ground lug GR-C101 (copper lug, painted yellow). "
         "Verify ground resistance less than 10 ohms using megohmmeter. "
         "Anti-static coveralls mandatory. No synthetic clothing."),

        ("3. PPE Requirements — OISD-105 Mandatory",
         "Per OISD-105 Section 4.1 and OSHA 1910.132: "
         "Minimum PPE for all compressor maintenance: "
         "Full face shield + safety glasses. Chemical-resistant gloves (nitrile 8mil). "
         "Flame-resistant coveralls (NFPA 70E Category 2 minimum). "
         "Steel-toed safety boots. Hard hat (Class E, electrical rated). "
         "Hearing protection (earmuffs, NRR 28 minimum). "
         "H2S detector (personal) — mandatory for gas service."),

        ("4. Confined Space Gas Testing and Ventilation",
         "Per OSHA 1910.146 and OISD-105 Section 8.2: "
         "Compressor crankcase is classified as a Permit-Required Confined Space. "
         "Atmospheric testing required before entry: O2 19.5–23.5%, LEL less than 10%, "
         "H2S less than 1 ppm (BPCL standard, stricter than OSHA 10 ppm TWA). "
         "Continuous forced ventilation (minimum 4 air changes/hour) required during work. "
         "Station attendant must be present outside confined space at all times. "
         "Rescue equipment (SCBA, rescue harness) to be staged at entry point."),

        ("5. Tagout Warning Flag Registration",
         "Per OSHA 1910.147 and BPCL PTW System Procedure PTW-BPCL-001: "
         "All lockout/tagout points must be registered in the PTW system before work begins. "
         "Tagout flags must be red with white text: DANGER — DO NOT OPERATE. "
         "Each tag must show: technician name, date, equipment tag, permit number. "
         "PTW Control Room copy must be maintained until all tags are removed. "
         "No tag removal without PTW closure and supervisor sign-off.")
    ]
)

# ── 5. WORK ORDERS CSV ────────────────────────────────────────────────────────
work_orders = [
    ["WO-2024-0847", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "BRG-WEAR",
     "High vibration at BPFI frequency (103 Hz) — 9.2 mm/s RMS exceeded Zone C limit",
     "R. Sharma", "A. Kumar", "2024-01-15", "2024-01-17", 14,
     "SKF 6316 (x2), SKF NU316 (x1), Mobil SHC 100 grease 1kg", "Inner race fatigue — operating hours 8,650",
     "COMPLETED"],
    ["WO-2024-0912", "P-202", "Crude Oil Transfer Pump (Standby)", "BPCL Mathura", "SEAL-FAIL",
     "Mechanical seal leakage — barrier fluid level dropped 25% in 8 hours",
     "M. Singh", "P. Verma", "2024-02-03", "2024-02-05", 16,
     "John Crane 2800 Seal Kit, O-ring set, Barrier fluid 5L", "Seal face wear — API Plan 53B pressure low",
     "COMPLETED"],
    ["WO-2024-1034", "C-101", "Natural Gas Reciprocating Compressor", "BPCL Mathura", "VIBR-HIGH",
     "High vibration on crankshaft — 12.1 mm/s at 2x RPM (misalignment signature)",
     "S.K. Sharma", "D. Yadav", "2024-03-10", "2024-03-12", 18,
     "Coupling insert (Falk T10), Alignment shims (set)", "Thermal misalignment — coupling wear",
     "COMPLETED"],
    ["WO-2024-1156", "T-301", "Crude Distillation Tower Overhead Condenser", "BPCL Mathura", "CORROSION",
     "Tube bundle corrosion — process side fouling, heat transfer reduced 30%",
     "V. Mishra", "K. Patel", "2024-04-01", "2024-04-07", 48,
     "Tube bundle T-301-B (spare), Gasket set, Chemical inhibitor 20kg", "Overhead corrosion — naphthenic acid",
     "COMPLETED"],
    ["WO-2024-1289", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "CAVITN",
     "Cavitation noise and fluctuating flow — suction pressure low, NPSH insufficient",
     "R. Gupta", "A. Kumar", "2024-05-20", "2024-05-20", 4,
     "None (operational adjustment)", "NPSH margin reduced — tank level low during transfer",
     "COMPLETED"],
    ["WO-2024-1445", "E-401", "Crude-Crude Heat Exchanger", "BPCL Mathura", "FOUL",
     "Shell side fouling — pressure drop increased 2.8 bar above design",
     "S. Kapoor", "N. Tiwari", "2024-06-15", "2024-06-18", 24,
     "Chemical cleaning solution 50L, Gasket set (x2)", "Asphaltene deposition on shell baffles",
     "COMPLETED"],
    ["WO-2024-1567", "P-203", "Naphtha Reflux Pump", "BPCL Mathura", "IMBALANCE",
     "High 1x vibration — impeller imbalance after hydro-blast cleaning",
     "R. Sharma", "B. Joshi", "2024-07-08", "2024-07-09", 10,
     "None (balance correction)", "Impeller fouling removal altered balance — required dynamic balancing",
     "COMPLETED"],
    ["WO-2024-1702", "C-102", "LPG Compressor", "BPCL Mathura", "BRG-WEAR",
     "Bearing temperature high — 94 degC on drive end, alarm at 85 degC",
     "A.K. Singh", "P. Verma", "2024-08-22", "2024-08-23", 12,
     "SKF 22320 spherical roller bearing (x1), Mobil SHC 460 grease 500g",
     "Overlubrication — grease churning and overheating", "COMPLETED"],
    ["WO-2024-1834", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "MISALIGN",
     "Coupling misalignment after maintenance — 2x vibration 6.8 mm/s",
     "R. Gupta", "A. Kumar", "2024-09-10", "2024-09-10", 6,
     "Alignment shims (set)", "Incorrect reassembly — pipe strain after flange reconnection",
     "COMPLETED"],
    ["WO-2024-1956", "V-501", "Crude Feed Control Valve", "BPCL Mathura", "VALVE-STICK",
     "Control valve sticking — poor response, hunting on flow control loop FC-201",
     "M. Kumar", "D. Yadav", "2024-10-05", "2024-10-06", 8,
     "Valve packing (PTFE, 25mm), Actuator diaphragm", "Packing seal dried out — crude service",
     "COMPLETED"],
    ["WO-2024-2089", "P-204", "Kerosene Product Pump", "BPCL Mathura", "SEAL-FAIL",
     "Single mechanical seal leak — visible weeping at gland",
     "S.K. Sharma", "K. Patel", "2024-11-01", "2024-11-02", 14,
     "Chesterton 442 seal kit, O-rings (Viton, set)", "Seal face chipped — foreign particle ingestion",
     "COMPLETED"],
    ["WO-2025-0023", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "BRG-WEAR",
     "Scheduled bearing replacement — 8,100 hours since last change (exceeded 8,000 hr limit)",
     "R. Gupta", "A. Kumar", "2025-01-12", "2025-01-14", 16,
     "SKF 6316 (x2), SKF NU316 (x1), Mobil SHC 100 grease 1kg, Coupling insert",
     "Preventive replacement — condition satisfactory (vibration 4.2 mm/s Zone B)", "COMPLETED"],
    ["WO-2025-0145", "T-302", "Vacuum Column", "BPCL Mathura", "VIBR-HIGH",
     "Column tray vibration — suspected tray damage from water ingestion",
     "V. Mishra", "N. Tiwari", "2025-02-20", "2025-02-28", 72,
     "Column tray sections (x12), Downcomer seal bars, Gaskets",
     "Water hammer event collapsed 12 trays — Unit 3 water ingestion incident", "COMPLETED"],
    ["WO-2025-0278", "C-101", "Natural Gas Reciprocating Compressor", "BPCL Mathura", "VALVE-FAIL",
     "Suction valve failure — gas bypass detected on 3rd stage cylinder",
     "A.K. Singh", "B. Joshi", "2025-03-15", "2025-03-17", 20,
     "Hoerbiger compressor valve (x4), Valve springs (x8), Cage plate",
     "Valve plate fatigue fracture — 24,000 operating hours", "COMPLETED"],
    ["WO-2025-0389", "P-202", "Crude Oil Transfer Pump (Standby)", "BPCL Mathura", "CORROSION",
     "Impeller corrosion — wall thickness reduced below minimum (2.1 mm measured, 3.0 mm minimum)",
     "R. Sharma", "P. Verma", "2025-04-08", "2025-04-12", 30,
     "Impeller (bronze, P/N PVXM-IMP-200), Wear ring set, Gaskets",
     "Naphthenic acid corrosion — crude API gravity increased to 28", "COMPLETED"],
    ["WO-2025-0512", "E-402", "Product Cooler", "BPCL Mathura", "LEAK",
     "Tube leakage — process fluid detected in cooling water circuit",
     "S. Kapoor", "D. Yadav", "2025-05-02", "2025-05-06", 32,
     "Tube plugs (x12), Tube sheet gasket", "Pitting corrosion — cooling water treatment failure",
     "COMPLETED"],
    ["WO-2025-0634", "P-205", "Diesel Transfer Pump", "BPCL Mathura", "CAVITN",
     "Intermittent cavitation at low tank levels — NPSH margin negative below 30% tank level",
     "M. Singh", "A. Kumar", "2025-06-10", "2025-06-11", 8,
     "None (operational procedure change)", "Tank drawdown below minimum operating level",
     "COMPLETED"],
    ["WO-2025-0756", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "BRG-TEMP",
     "Drive end bearing temperature alarm — 87 degC during startup after turnaround",
     "R. Gupta", "K. Patel", "2025-07-01", "2025-07-01", 3,
     "Mobil SHC 100 grease 500g", "Over-packing after turnaround — excess grease churning",
     "COMPLETED"],
    ["WO-2025-0889", "C-101", "Natural Gas Reciprocating Compressor", "BPCL Mathura", "OIL-LEAK",
     "Crankcase oil leak at crankshaft seal — oil mist detected in compressor bay",
     "S.K. Sharma", "B. Joshi", "2025-07-18", "2025-07-19", 14,
     "Crankshaft seal (Viton lip seal, 80x100x10), Oil (5L Shell Tellus S2)",
     "Lip seal worn — 32,000 hours service", "COMPLETED"],
    ["WO-2025-1012", "P-201", "Crude Oil Transfer Pump", "BPCL Mathura", "VIBR-HIGH",
     "High vibration alarm — 8.4 mm/s RMS at bearing, BPFI frequency elevated",
     "R. Gupta", "A. Kumar", "2025-08-05", None, 0,
     "SKF 6316 bearing (on order)", "Suspected inner race fatigue — bearing at 4,200 hours since last change",
     "OPEN"],
]

wo_path = os.path.join(SAMPLE_DIR, "work_orders_bpcl.csv")
with open(wo_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["WO_ID", "Asset_ID", "Asset_Name", "Plant", "Failure_Code",
                     "Failure_Description", "Reported_By", "Technician",
                     "Start_Date", "End_Date", "Hours_Spent", "Parts_Used",
                     "Root_Cause", "Status"])
    writer.writerows(work_orders)
print(f"✅ Created {wo_path} ({len(work_orders)} work orders)")

# ── 6. RCA REPORTS JSON ───────────────────────────────────────────────────────
rca_reports = [
    {
        "report_id": "IIR-BPCL-MTR-2022-019",
        "date": "2022-11-14",
        "asset_id": "P-201",
        "incident_title": "P-201 Mechanical Seal Failure Causing Process Fluid Release",
        "severity": "HIGH",
        "incident_description": (
            "P-201 mechanical seal failed catastrophically at 02:30 hrs on 12-Nov-2022. "
            "Crude oil released at approximately 15 LPM for 8 minutes before operator isolation. "
            "Approx. 120 litres of crude oil spilled in pump bay. No personnel injuries. "
            "Fire watch mobilized. Plant fire brigade attended. Environmental report filed."
        ),
        "root_cause": (
            "Reverse flow through pump during isolation allowed crude oil to flash "
            "across seal faces. Post-incident investigation confirmed that the LOTO "
            "sequence used was suction-first (STEP A then B per Rev.2 SOP), which "
            "caused high-pressure discharge fluid to reverse through the pump before "
            "the discharge valve was closed. This overpressured the seal chamber "
            "and caused catastrophic seal face fracture."
        ),
        "contributing_factors": [
            "LOTO sequence in SOP-P201-MAINT-001 Rev.2 (2019) was suction-first — incorrect for this pump configuration",
            "Operator followed documented procedure exactly — procedure was at fault, not the operator",
            "API 610-12th Edition (2021) recommends discharge-first isolation for back-pressure protection",
            "Seal barrier fluid pressure alarm was not functioning (failed transmitter PT-201-SL)"
        ],
        "corrective_actions": [
            "Revised LOTO sequence: discharge valve first, then suction — issued as SOP Rev.3 (Jan 2023)",
            "Replaced seal barrier fluid pressure transmitter PT-201-SL",
            "Added second pressure indicator PI-201-SL as backup",
            "All operators retrained on revised LOTO sequence — training records in SAP HR",
            "Emergency spill kit relocated to pump bay (previously 50m away)"
        ],
        "recurrence_prevention": (
            "SOP revised to discharge-first LOTO sequence (STEP B then A). "
            "Quarterly LOTO drill introduced for all pump operators. "
            "Barrier fluid transmitter replaced and added to critical instrument list "
            "with monthly function testing. Spill containment bund capacity review initiated."
        ),
        "lessons_learned": [
            "Always verify LOTO sequence against latest approved SOP revision — not from memory",
            "Discharge-first isolation is standard practice for pumps with potential for reverse flow",
            "Instrument failure (PT-201-SL) masked the seal distress for 3 hours before failure"
        ],
        "approved_by": "A.K. Singh, Head Reliability Engineering — BPCL Mathura",
        "distribution": ["Operations Manager", "Safety Officer", "Mechanical Maintenance", "Process Engineering"]
    },
    {
        "report_id": "IIR-BPCL-MTR-2023-007",
        "date": "2023-04-22",
        "asset_id": "C-101",
        "incident_title": "C-101 Unplanned Shutdown — Suction Valve Failure, 3rd Stage",
        "severity": "MEDIUM",
        "incident_description": (
            "C-101 natural gas compressor tripped on high discharge temperature at 14:15 hrs. "
            "Investigation revealed 3rd stage suction valve failure — valve plate fractured. "
            "Gas bypass across failed valve caused temperature rise from 165 to 210 degC. "
            "High temperature trip protected the machine. Unit 3 gas recovery offline 36 hours."
        ),
        "root_cause": (
            "Hoerbiger suction valve on 3rd stage cylinder had accumulated 26,200 operating hours "
            "against a recommended replacement interval of 20,000 hours. "
            "Valve plate material fatigue — crack initiated at bolt hole and propagated across plate. "
            "Valve replacement was deferred twice due to lack of spare parts availability."
        ),
        "contributing_factors": [
            "Valve replacement deferred at 20,000 hr mark (spare not available — SAP stock-out)",
            "Deferred maintenance not escalated to Maintenance Manager — stayed as open work order",
            "No condition monitoring on compressor valves (temperature trending only, no vibration per cylinder)",
            "Spare parts minimum stock level for Hoerbiger valves was set to 0 — now corrected"
        ],
        "corrective_actions": [
            "All 4 suction valves and 4 discharge valves replaced (complete valve overhaul)",
            "SAP minimum stock level for Hoerbiger valves set to 2 sets",
            "Deferred maintenance escalation procedure introduced: 30 days overdue → Maintenance Manager mandatory review",
            "Cylinder-level temperature monitoring added (4 new thermocouples installed)"
        ],
        "recurrence_prevention": (
            "Valve replacement interval reduced to 18,000 hours (10% margin below 20,000 hr limit). "
            "Spare valve inventory reviewed for all reciprocating compressors across the refinery. "
            "Maintenance deferral tracking added to monthly KPI dashboard for Department Head review."
        ),
        "lessons_learned": [
            "Critical spare parts stock-out is a major risk — minimum stock levels must be enforced in SAP",
            "Deferred maintenance must be formally escalated — cannot remain as passive open WO",
            "Cylinder-level temperature trending would have given 8–12 hours early warning"
        ],
        "approved_by": "V.P. Mishra, Head Maintenance — BPCL Mathura",
        "distribution": ["Operations", "Maintenance", "Materials Management", "Safety"]
    },
    {
        "report_id": "IIR-BPCL-MTR-2023-015",
        "date": "2023-08-30",
        "asset_id": "T-302",
        "incident_title": "T-302 Vacuum Column Tray Damage — Water Ingestion Event",
        "severity": "HIGH",
        "incident_description": (
            "Water ingestion event at 09:45 hrs caused column tray damage in T-302 vacuum column. "
            "12 of 42 trays damaged by water hammer. Column taken offline for tray replacement. "
            "Production loss: 4,800 MT crude throughput over 9-day shutdown. "
            "Estimated financial impact: INR 18.5 Crore."
        ),
        "root_cause": (
            "Cooling water tube failure in overhead condenser E-301 allowed cooling water "
            "ingestion into the vacuum column overhead stream. Water accumulated in reflux drum "
            "V-301 and was inadvertently pumped back to the column as reflux. "
            "At column bottom temperature of 340 degC, water flashed to steam — "
            "rapid pressure rise caused hydraulic hammer and tray collapse."
        ),
        "contributing_factors": [
            "E-301 cooling water tube had visible wall thinning at last inspection (18 months prior) — not replaced",
            "Reflux drum V-301 had no water detection (density or conductivity measurement)",
            "Operator did not check reflux composition when column pressure fluctuated",
            "No high-differential-pressure alarm across column trays"
        ],
        "corrective_actions": [
            "12 damaged trays replaced (TK-302-TRAY-019 through TK-302-TRAY-030)",
            "E-301 tube bundle replaced — all tubes with wall thickness less than 2.5mm replaced proactively",
            "Conductivity analyser installed on V-301 reflux drum to detect water ingestion",
            "High dP alarm added across column sections 1–3 and 4–7",
            "Tray thickness measurement frequency increased from annual to 6-monthly"
        ],
        "recurrence_prevention": (
            "Heat exchanger tube thickness criterion tightened: replace when below 2.8mm (was 2.0mm). "
            "All overhead condensers added to critical equipment list with 6-monthly tube inspection. "
            "Water ingestion response procedure added to emergency operating procedures."
        ),
        "lessons_learned": [
            "Deferred maintenance on heat exchanger with known tube thinning directly caused the event",
            "Early detection instruments (conductivity, water cut) are low-cost insurance",
            "Financial impact of deferred maintenance (18.5 Cr) vastly exceeded repair cost (1.2 Cr)"
        ],
        "approved_by": "A.K. Singh and R. Nair (Process Engineering) — BPCL Mathura",
        "distribution": ["All Department Heads", "Refinery Manager", "HPCL Engineering (Corporate)"]
    },
    {
        "report_id": "IIR-BPCL-MTR-2024-003",
        "date": "2024-02-15",
        "asset_id": "P-202",
        "incident_title": "P-202 Bearing Failure During Standby Run — Improper Storage",
        "severity": "MEDIUM",
        "incident_description": (
            "P-202 (standby crude transfer pump) failed on bearing during monthly test run. "
            "Bearing seized within 8 minutes of startup — caused motor overload trip. "
            "Post-failure bearing analysis showed fretting corrosion on outer race. "
            "P-202 unavailable for 5 days pending bearing replacement. "
            "Risk: P-201 was running without standby cover during this period."
        ),
        "root_cause": (
            "P-202 had been in standby mode for 8 months without being rotated. "
            "Static load on bearing at same position for 8 months caused fretting corrosion "
            "(false brinelling) at rolling element contact points. "
            "Monthly test run procedure did not specify minimum run duration or rotation schedule."
        ),
        "contributing_factors": [
            "Standby pump rotation procedure did not exist — only monthly test run (no minimum duration)",
            "No scheduled bearing rotation (jog) during extended standby periods",
            "P-202 SAP equipment strategy was copied from P-201 strategy without standby-specific requirements",
            "Bearing storage period exceeded SKF recommendation of 6 months without rotation"
        ],
        "corrective_actions": [
            "Bearing replaced on P-202 — all four bearings replaced (not just failed bearing)",
            "Standby pump rotation schedule introduced: 30-minute run every 2 weeks (minimum)",
            "Monthly test run extended to 2 hours minimum",
            "All standby pump strategies reviewed and updated in SAP PM",
            "Bearing shaft rotation log added to standby pump PM checklist"
        ],
        "recurrence_prevention": (
            "Standby pump management standard issued (BES-ME-012) covering: "
            "minimum run duration, rotation frequency, bearing inspection on startup after 3+ months idle. "
            "SAP PM plans updated for all critical standby rotating equipment."
        ),
        "lessons_learned": [
            "Static standby is as damaging as overloading — bearings need regular rotation",
            "Standby equipment strategies need different PM requirements than running equipment",
            "Single-point failure risk: when standby is unavailable, the risk profile changes significantly"
        ],
        "approved_by": "V.P. Mishra, Head Maintenance — BPCL Mathura",
        "distribution": ["Mechanical Maintenance", "Reliability Engineering", "Operations"]
    },
    {
        "report_id": "IIR-BPCL-MTR-2024-011",
        "date": "2024-06-28",
        "asset_id": "P-201",
        "incident_title": "P-201 Unplanned Shutdown — Cavitation at Low Tank Level",
        "severity": "LOW",
        "incident_description": (
            "P-201 vibration alarm triggered at 23:15 hrs followed by shutdown 12 minutes later. "
            "Vibration reached 11.8 mm/s RMS (Zone D — shutdown setpoint). "
            "Root cause identified as cavitation. No equipment damage. "
            "Pump restarted within 2 hours after tank level restored above minimum."
        ),
        "root_cause": (
            "Tank TK-101 crude oil level fell to 2.1m (below minimum 2.5m operating level) "
            "during a transfer operation. At this level, NPSH available (3.8m) dropped below "
            "NPSH required (4.2m) for P-201, causing vapour cavitation. "
            "Night shift operator was not aware of the NPSH margin issue at low tank levels."
        ),
        "contributing_factors": [
            "No low NPSH margin alarm — only vibration alarm was available",
            "Tank level low alarm setpoint was 2.0m — below the 2.5m minimum for P-201 operation",
            "Night shift operator not trained on the relationship between tank level and NPSH",
            "Operating envelope for P-201 NPSH vs tank level not documented in control room"
        ],
        "corrective_actions": [
            "TK-101 low level alarm setpoint raised from 2.0m to 2.8m for P-201 operation",
            "NPSH margin calculation curve posted in control room and shared with all operators",
            "Night shift operator training on NPSH and cavitation added to onboarding checklist",
            "NPSH margin indicator added to DCS faceplate for P-201"
        ],
        "recurrence_prevention": (
            "Operating procedure for TK-101-to-CDU transfer updated with minimum tank level requirement. "
            "All pump operating envelopes reviewed for NPSH margin — 3 additional pumps identified "
            "with similar risk and alarm setpoints corrected."
        ),
        "lessons_learned": [
            "Vibration-only protection is too late — NPSH margin monitoring is the right leading indicator",
            "Operating envelopes (not just process limits) must be communicated to shift operators",
            "A low-cost alarm setpoint change prevented a repeat event that could have caused seal damage"
        ],
        "approved_by": "R. Gupta, Lead Mechanical Engineer — BPCL Mathura",
        "distribution": ["Operations", "Mechanical Maintenance", "Process Safety"]
    }
]

rca_path = os.path.join(SAMPLE_DIR, "rca_reports_bpcl.json")
with open(rca_path, "w", encoding="utf-8") as f:
    json.dump(rca_reports, f, indent=2, ensure_ascii=False)
print(f"✅ Created {rca_path} ({len(rca_reports)} RCA reports)")

print("\n✅ All synthetic data generated successfully!")
print(f"   Location: {SAMPLE_DIR}")
print("   Files:")
for fn in os.listdir(SAMPLE_DIR):
    fp = os.path.join(SAMPLE_DIR, fn)
    print(f"     {fn} ({os.path.getsize(fp):,} bytes)")
