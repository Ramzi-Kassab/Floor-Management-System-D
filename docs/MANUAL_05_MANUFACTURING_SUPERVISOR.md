# Manufacturing Supervisor — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** Manufacturing Supervisor — oversees new drill bit manufacture (L3, L4, and L5.5 levels), manages designs and BOMs, and coordinates production planning for new-build work orders.

---

## 1. Your Role in the System

As a Manufacturing Supervisor, you are responsible for the technical foundation of every new drill bit that ARDT produces. You manage the designs (L3 and L4 blueprints), create and maintain Bills of Materials (BOMs at L5 level), and ensure that the correct cutter specifications are assigned before a bit enters production. Your work in the system directly feeds the Production Planner and the Work Order lifecycle.

You also serve as the bridge between engineering documentation and the shop floor. When Halliburton sends a PDF specification for a new bit design, you use the Cutter Map tool to extract cutter data from that PDF, review it, and convert it into a formal BOM that the rest of the system can use. This ensures that every bit manufactured at ARDT has a complete, traceable material specification.

Your daily interaction with the system centers on the Technology module (Designs, BOMs, HDBS Types) and the Cutter Map. You also participate in the Production Planner by verifying that manufacture bits have BOMs assigned before they can be scheduled, and you may create work orders for L3/L4 manufacture jobs.

---

## 2. Logging In

1. Open your web browser and go to **http://localhost:8001**.
2. You will see the ARDT login page. Enter your **Username** and **Password** (provided by your administrator).
3. Click the **Log In** button.
4. After successful login, you will be taken to the main dashboard. The left sidebar shows all available modules.

If you have forgotten your password, contact your system administrator to reset it.

---

## 3. Your Workbench

After logging in, your primary areas of work are accessible from the left sidebar:

- **Technology** section (blue gear icon):
  - **Designs** — view and manage all drill bit designs (L3, L4, L5.5).
  - **BOMs** — view, create, and manage Bills of Materials (L5).
  - **HDBS Types** — reference list of Halliburton Drill Bit System classification codes.
  - **SMI Types** — Standard Material Identifier types.

- **Cutter Map** — the PDF extraction and BOM creation tool, where you import Halliburton PDFs and build BOMs visually.

- **Production** section:
  - **Production Planner** — view planned and scheduled work, verify BOM readiness.
  - **Work Orders** — create and monitor manufacture work orders.
  - **Drill Bits** — the master list of all registered drill bits.

- **Inventory** section:
  - **PDC Cutters** — the cutter inventory dashboard showing stock levels by variant.

The **notification bell** in the top navigation bar shows real-time alerts when work orders are approved, evaluations are completed, or other events relevant to your role occur.

---

## 4. Core Workflows

### 4.1 Viewing and Managing Designs

1. In the sidebar, click **Technology > Designs**.
2. The design list shows all registered designs with columns for Level (L3, L4, L5.5), MAT Number, HDBS Type, Size, Status, and number of BOMs.
3. Click any design row to view its full detail, including pocket definitions and linked BOMs.
4. To create a new design, click the **New Design** button and fill in the required fields: name, order level (L3/L4/L5.5), MAT number, size, and HDBS type.

### 4.2 Creating a BOM from a Halliburton PDF

This is one of your most important workflows. It converts a Halliburton PDF specification into a structured BOM.

1. Go to **Technology > BOMs** and click **Create BOM**.
2. You will see a design selection table. Use the column filters and search to find the correct design. Click the design row to select it.
3. Click **Open Cutter Map**. This opens the Cutter Map tool with the selected design pre-loaded.
4. In the Cutter Map, click the **Upload PDF** button and select the Halliburton PDF file.
5. The system extracts cutter data automatically: blade layouts, cutter positions, group assignments, and shape images.
6. Review the extracted data on screen. Each blade is shown with its cutter positions. You can:
   - Click a cutter position to change the assigned MAT number.
   - Use the **Select Cutter MAT** dialog (powered by live inventory data) to pick from available cutters.
   - Toggle the **Available Only** filter to see cutters currently in stock.
   - Check the **Used for Design** toggle to see cutters previously used for this design family.
7. When satisfied, click **Create BOM** (or **Update BOM** if revising an existing one).
8. In the **Review BOM Before Saving** modal:
   - Verify or set the **SMI Type** (use the picker to search or quick-create).
   - Set the **IADC Code** from the dropdown (or quick-add a new one).
   - Set the **Status** (Draft, Active, or Obsolete).
9. Click **Save**. The BOM is created with all cutter lines and the source PDF data stored for reference.
10. If any cutters from the PDF are not in the inventory, you will be redirected to the **Add Cutter Wizard** to register them.

### 4.3 Reviewing and Editing an Existing BOM

1. Go to **Technology > BOMs** and click on any BOM row.
2. The BOM detail page shows all BOM lines (cutter requirements) and the design context.
3. To edit in the Cutter Map view, click the **Open in Cutter Map** link. This opens the BOM with the blade layout and cutter assignments editable.
4. Make changes as needed and click **Update BOM** to save.

### 4.4 Registering a New Manufacture Drill Bit

1. Go to **Drill Bits** in the sidebar and click **Register New Bit**.
2. Enter the serial number (6 digits for Roller Cone, 8 digits for Fixed Cutter).
3. Select the Design from either the **From Design** or **From BOM** tab.
4. Select the BOM if applicable (this assigns both brazing BOM and system BOM).
5. Click **Register**. You will be taken to the First Event Wizard.
6. Choose the initial event: **Received**, **Intake**, **In Production**, or **Skip**.
7. The drill bit is now registered and ready for production planning.

### 4.5 Assigning a BOM to a Drill Bit

If a drill bit was registered without a BOM, it will appear in the **BOM Pending** queue on the Receiving Dashboard.

1. Go to the drill bit detail page (click the serial number in any list).
2. Click the **Brazing BOM** or **System BOM** field — it is clickable.
3. A dropdown appears with all BOMs for that design. Select the correct BOM.
4. The assignment saves immediately. A confirmation message appears.

Alternatively, resolve it from **Receiving > BOM Pending**:
1. Find the pending request and click **Resolve**.
2. Select the BOM to assign.

### 4.6 Adding a Bit to the Production Planner

1. Go to **Drill Bits** and find the bit you want to schedule.
2. Click the **Business Unit** badge (or pencil icon) to open the assignment modal.
3. Select the correct Business Unit (e.g., LSTK, ARDT, L3, L4).
4. Choose **New** or **Repair** as the work type.
5. Click **Assign & Add to Planner**. The bit appears in the Planner's Planned tab.

**Important:** Fixed Cutter (FC) bits without a BOM cannot be added to the planner. You will see an orange warning. Assign a BOM first.

### 4.7 Creating a Work Order

1. Go to **Work Orders > Create Work Order**.
2. Select the **Account** (Business Unit) — this determines the WO number format and workflow type.
3. Enter the **Serial Number**. The system auto-populates: size, type, HDBS, SMI, design, BOM, and repair/rerun counts.
4. Verify all pre-filled fields. Click **Create Work Order**.
5. The work order is created in **Pending** status, ready for release and approval.

---

## 5. Forms & Data Entry Reference

| Form / Page | Location | Key Fields |
|---|---|---|
| Design Create | Technology > Designs > New | Name, Order Level (L3/L4/L5.5), MAT Number, Size, HDBS Type, Status |
| BOM Create | Technology > BOMs > Create BOM | Design selection, then Cutter Map extraction |
| Review BOM Modal | Inside Cutter Map after Create/Update | SMI Type, IADC Code, Status, System MAT, Brazing MAT |
| Drill Bit Register | Drill Bits > Register New | Serial Number, Design, BOM (optional) |
| WO Create | Work Orders > Create | Account, Serial Number (auto-populates remaining fields) |
| BU Assignment Modal | Drill Bit list or detail page | Business Unit, New/Repair, Requester, Justification |

---

## 6. Reports Available to You

| Report | Location | Description |
|---|---|---|
| Design List | Technology > Designs | All designs with level, MAT, size, status, BOM count |
| BOM List | Technology > BOMs | All BOMs with design, MAT numbers, status, line count |
| PDC Cutter Inventory | Inventory > PDC Cutters | Full cutter stock by variant with consumption history |
| Cutter Inventory Export | PDC Cutters > Export Excel | Excel download with column/record filtering options |
| Drill Bit List | Drill Bits (with export) | All registered bits with design, BOM, status, location |
| Production Planner | Production > Planner | Planned, scheduled, and in-progress production entries |
| BOM Pending Queue | Receiving > BOM Pending | Bits awaiting BOM assignment |

---

## 7. Notifications & Alerts

You will receive notifications for:

- **BOM Pending Request** — when a new manufacture bit is registered without a BOM, a request appears in the BOM Pending queue.
- **Work Order Approved** — when a manager approves a work order you created, you receive a notification with a link to the router sheet.
- **Evaluation Completed** — when an evaluation is finished on a bit under your supervision.
- **GRN Posted** — when new cutter stock is received.

Notifications appear as a badge on the bell icon in the top navigation. Click the bell to see recent alerts, and click **View All** for the full notification list.

---

## 8. Approvals & Sign-offs

- **BOM Status**: You can set a BOM to **Draft**, **Active**, or **Obsolete** in the Review BOM modal. Only Active BOMs should be used in production.
- **Design Status**: Similarly, designs progress from Draft to Active. An Obsolete design cannot be reactivated.
- **Work Order Release**: After creating a WO, you may click **Mark as Released** to confirm that the physical transaction is ready. A manager then approves the WO to make it Active.
- **BOM Pending Resolution**: You sign off on a BOM Pending request by assigning a BOM and resolving the queue entry.

---

## 9. Frequently Asked Questions

**Q: I uploaded a PDF but some cutters are not recognized. What do I do?**
A: The system redirects you to the Add Cutter Wizard. Follow the steps to register the missing cutters in inventory. You can also add them later from the Inventory module and re-open the BOM in the Cutter Map.

**Q: Can I edit a BOM after it has been set to Active?**
A: Yes. Open the BOM in the Cutter Map, make your changes, and click Update BOM. You can also change the status back to Draft if major revisions are needed, though this should be done carefully if production has already started.

**Q: What is the difference between L3, L4, and L5.5?**
A: L3 is a base design with no cutter specifications. L4 includes pocket positions for cutters. L5.5 is a brazed head that still needs sub-arc welding and machining — it is an intermediate stage between a BOM and a finished bit.

**Q: How do I know if a bit is ready for the planner?**
A: Fixed Cutter bits must have a BOM assigned. Check the BOM Pending queue or the bit's detail page. If the Brazing BOM or System BOM fields are empty, the bit is not ready.

**Q: Where do I see what cutters are available for a new BOM?**
A: In the Cutter Map, the Select Cutter MAT dialog shows live inventory with stock levels by variant (New, Reclaimed, Ground, etc.), on-order quantities, and design usage history.

**Q: Can I create a design directly from the Cutter Map?**
A: No. Designs must be created first in the Technology > Designs page. The Cutter Map only creates BOMs for existing designs.

**Q: What happens when I click "Save & go to BOMs List" in the review modal?**
A: The BOM is saved and you are redirected to the full BOMs list page, where you can verify the new entry.

---

## 10. Glossary

| Term | Definition |
|---|---|
| **BOM (Bill of Materials)** | A complete specification of all cutters needed for a drill bit design (L5 level). |
| **Cutter Map** | The tool that extracts cutter data from Halliburton PDFs and creates BOMs. |
| **Design** | The blueprint for a drill bit, defining its geometry and pocket positions (L3/L4). |
| **HDBS Type** | Halliburton Drill Bit System code — a classification for cutter families. |
| **L3 / L4 / L5 / L5.5** | Order levels: L3 = base design, L4 = design with pockets, L5 = complete BOM, L5.5 = brazed head needing welding. |
| **MAT Number** | Material number — the unique identifier for a design or BOM (e.g., 1283567M1). |
| **PDC Cutter** | Polycrystalline Diamond Compact cutter — the cutting element inserted into drill bit pockets. |
| **SMI Type** | Standard Material Identifier — a specific cutter configuration code. |
| **Variant** | A stock category for a cutter (e.g., New Purchased, Used Reclaimed, Client New). |
| **Production Planner** | The scheduling tool that queues drill bits for manufacture or repair work orders. |
| **Business Unit (BU)** | An account category (LSTK, ARAMCO, L3, L4, etc.) that determines WO numbering and workflow type. |
