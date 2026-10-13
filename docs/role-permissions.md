# Nyaya-Tula AI — Role-Based Access Control (RBAC)

The system implements strict role-based access for border checkpoint operations:

| Role | Permissions | Use Case |
| :--- | :--- | :--- |
| **Inspector (Border Officer)** | Upload documents, run screening pipeline, inspect 100 checks, view risk scores, trigger rescan, submit clearance decisions. | Frontline immigration counters, e-gates. |
| **Verifier (Secondary Review)** | Review flagged `SECONDARY_SCRUTINY` cases, examine unreadable fields, override check digit flags with manual justification. | Secondary inspection rooms, supervisor desks. |
| **Administrator** | Manage checkpoint settings, view complete audit ledger, export encrypted CSV/ZIP dossiers, configure API gateways. | System administrators, audit officers. |
