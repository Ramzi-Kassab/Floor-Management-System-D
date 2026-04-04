# System Trigger Points Catalog
## Every action in the system that can trigger notifications/workflow actions

### RECEIVING
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 1 | package-plus | Create Backload Batch | /work-orders/receiving/batches/create/ | BIT_RECEIVED | Receiving Staff |
| 2 | check-circle | Confirm Batch Item | Batch Detail | BIT_RECEIVED | Receiving Staff |
| 3 | clipboard-check | Complete Receiving Inspection | Inspection Form | INSPECTION_ACCEPTED / INSPECTION_REJECTED | Inspector |
| 4 | alert-triangle | Cerebro Device Detected | Auto (during backload) | CEREBRO_DETECTED | System |

### PLANNING
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 5 | calendar-plus | Add Bit to Planner | Drill Bit List/Detail | ADDED_TO_PLAN | Planner |
| 6 | rocket | Release from Planner | Production Planner | WO_RELEASED | Planner |
| 7 | arrow-right-left | Confirm Bit Transfer | Location Transfers | TRANSFER_CONFIRMED | Operator |
| 8 | check-circle | Confirm Release (at destination) | Location Transfers | TRANSFER_CONFIRMED | Operator |

### APPROVAL
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 9 | shield-check | Approve Work Order | WO Detail | WO_APPROVED | Manager |
| 10 | x-circle | Reject Work Order | WO Detail | WO_REJECTED | Manager |
| 11 | package-check | Mark WO as Released | WO Detail | WO_RELEASED | Manager |
| 12 | trash-2 | Delete Work Order | WO Detail | WO_DELETED | Manager |

### PRODUCTION
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 13 | play | Start Router Step | Router Sheet / Step Detail | WO_STARTED | Operator |
| 14 | check-circle | Complete Router Step | Step Detail | STEP_COMPLETED | Operator |
| 15 | skip-forward | Skip Router Step | Step Detail | STEP_COMPLETED | Operator/Supervisor |
| 16 | pause-circle | Put Step on Hold | Step Detail | STEP_ON_HOLD | Operator |
| 17 | play | Resume Step | Step Detail | STEP_RESUMED | Supervisor |
| 18 | shield-check | Request QC Review | Step Detail | STEP_WAITING_QC | Operator |
| 19 | check-circle | Request Approval | Step Detail | STEP_WAITING_APPROVAL | Operator |
| 20 | cpu | Request Tech Review | Step Detail | STEP_WAITING_TECH | Operator |
| 21 | check-circle-2 | All Steps Complete | Router Sheet (auto) | ALL_STEPS_DONE | System |

### EVALUATIONS
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 22 | check-circle | Complete Evaluation | Cutter Eval Matrix | EVALUATION_COMPLETED | Evaluator |
| 23 | flag | Report Issue (from DC) | Die Check Page | DIE_CHECK_DECISION | Operator/QC |
| 24 | flag | Report Issue (from Eval) | PDC Evaluation | DIE_CHECK_DECISION | Evaluator |
| 25 | flag | Report Issue (from Step) | Step Detail | DIE_CHECK_DECISION | Operator |

### QC & COMPLETION
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 26 | send | Send WO to QC | WO Detail | WO_SENT_TO_QC | Production Lead |
| 27 | check-circle | QC Pass | WO Detail | QC_PASSED | QC Inspector |
| 28 | x-circle | QC Fail | WO Detail | QC_FAILED | QC Inspector |
| 29 | check-circle-2 | Complete WO | WO Detail | WO_COMPLETED | Production Lead |

### QUALITY
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 30 | scale | Quality Decision (Accept) | Quality Issue Detail | — | QC Manager |
| 31 | alert-octagon | Quality Decision (Create NCR) | Quality Issue Detail | — | QC Manager |
| 32 | refresh-cw | Quality Decision (Rework) | Quality Issue Detail | — | QC Manager |

### INVENTORY
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 33 | check-circle | Post GRN | GRN Detail | GRN_POSTED | Warehouse Staff |

### ROUTE
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 34 | git-branch | Route Auto-Updated | Auto (after eval) | ROUTE_UPDATED | System |

### SPECIAL
| # | Icon | Action | Page | Event Code | Who Triggers |
|---|------|--------|------|-----------|-------------|
| 35 | alert-octagon | Critical Special Instruction | Router Step (auto) | SPECIAL_INSTRUCTION | System |
