# System Administrator — User Manual

**System:** ARDT Floor Management System
**Version:** Draft 1.0
**Date:** April 4, 2026
**Audience:** System Administrator — The person responsible for user accounts, system configuration, data seeding, backups, and overall system health.

---

## 1. Your Role in the System

As the System Administrator, you are the gatekeeper of the ARDT Floor Management System. You control who has access to the system, what each person can do, and how the underlying data is structured. Every other user in the organization depends on your work to ensure their login credentials function, their role-based permissions are correctly assigned, and the system data is backed up and recoverable.

Your responsibilities span three main areas. First, **user and access management**: creating user accounts, assigning roles (such as Operator, QC Inspector, or Operations Manager), and managing permissions that control which pages and actions each role can perform. Second, **system configuration**: setting up reference data such as business unit accounts, master processes, locations, and inventory categories that the rest of the system depends on. Third, **system maintenance**: performing database backups, running seed commands to populate initial data, monitoring system health, and troubleshooting login or access issues reported by staff.

You have the highest level of access in the system, including the Django Administration panel at `/admin/`. Use this access carefully, as changes in the admin panel directly affect the database.

---

## 2. Logging In

**Step 1.** Open your web browser (Chrome or Edge recommended) and navigate to:
`http://localhost:8001/accounts/login/`

**Step 2.** Enter your **Username** and **Password**. The default password for initial accounts is `Ardt@2025`.

**Step 3.** Click the **Log In** button. You will be taken to the Main Dashboard.

**Troubleshooting:**

| Problem | Solution |
|---------|----------|
| "Invalid username or password" | Verify the username is typed exactly (usernames are case-sensitive). Check Caps Lock. |
| Page does not load at all | Confirm the server is running. Ask the IT team to verify the process on port 8001. |
| "Your session has expired" | Sessions last 24 hours. Simply log in again. |
| User locked out | Go to **Users & Access > Users**, find the user, and ensure their account is marked Active. If they forgot their password, use the Reset Password function. |
| The page looks broken or unstyled | Try a hard refresh (Ctrl+Shift+R). Ensure you are using a modern browser. |

---

## 3. Your Workbench

After logging in, you see the **Main Dashboard**. The interface has three key areas:

**Top Navigation Bar:** Contains the ARDT logo and version number (FMS v5.4), a global search bar (Ctrl+K to focus), the dark mode toggle (moon/sun icon), the notification bell (updates every 10 seconds), a tasks link, and your user profile menu (click your initials to access Profile, Settings, or Sign Out).

**Left Sidebar:** A collapsible menu organized into sections. The sections most relevant to you are:
- **Dashboard** — Main, Manager, Planner, Technician, and QC dashboards
- **HR & Admin** — Employee records, attendance, competency matrix
- **Logistics > Setup** — Categories, attributes, variant cases, units of measure, locations, and other master data
- **Users & Access** (under the profile menu or at `/accounts/users/`) — User, Role, and Permission management

**Main Content Area:** Displays the active page. Pages update partially without full reloads, so changes feel immediate.

**Django Admin Panel:** Accessible at `http://localhost:8001/admin/`. This gives you direct database-level access to all models. Use it for bulk operations or troubleshooting that cannot be done through the regular interface.

---

## 4. Core Workflows

### 4.1 Creating a New User Account

**When:** A new employee joins ARDT and needs system access.

1. Navigate to **Users & Access > Users** (sidebar or `/accounts/users/`).
2. Click the **Create User** button at the top right.
3. Fill in the required fields:
   - **Username** (typically `firstname.lastname`, e.g., `j.smith`)
   - **Password** and **Confirm Password**
   - **First Name** and **Last Name**
   - **Email Address**
   - **Department** (select from dropdown)
   - **Position** (select from dropdown)
4. Set **Is Active** to checked (enabled by default).
5. Click **Save**.
6. After saving, you will be taken to the user's detail page.

**What happens next:** The user can immediately log in with the credentials you set.
**Who is notified:** No automatic notification is sent. You should inform the new user of their username and password directly.
**Common mistakes:** Forgetting to set the user as Active. Choosing a username that already exists (the system will show an error).

### 4.2 Assigning Roles to a User

**When:** After creating a user, or when an existing user's responsibilities change.

1. Go to **Users & Access > Users** and click on the user's name.
2. On the user detail page, find the **Roles** section.
3. Click the **Manage Roles** button (or navigate to `/accounts/users/<pk>/roles/`).
4. You will see a list of all available roles with checkboxes.
5. Check the roles that apply to this user (e.g., OPERATOR, QC_INSPECTOR).
6. Click **Save Changes**.

**Available roles include:** OPERATOR, PDC_SUPERVISOR, MFG_SUPERVISOR, OPS_MANAGER, QC_INSPECTOR, GENERAL_MANAGER, RECEIVING_CLERK, SYSTEM_ADMIN, PLANNER, HR_ADMIN, WAREHOUSE_CLERK, TECH_REP, and others.

**What happens next:** The user's access is updated immediately on their next page load.
**Common mistakes:** Assigning too many roles to one person. Each role grants specific capabilities, so assign only what is needed.

### 4.3 Resetting a User's Password

1. Go to **Users & Access > Users** and click on the user's name.
2. Click the **Reset Password** button.
3. Enter a new temporary password and confirm it.
4. Click **Save**.

**Important:** Inform the user of their new password and advise them to change it via **Profile > Settings > Password Change** after logging in.

### 4.4 Managing Roles and Permissions

**Viewing Roles:** Navigate to **Users & Access > Roles** (`/accounts/roles/`). Each role card shows its name, code, description, and how many users are assigned.

**Creating a New Role:**
1. Click **Create Role**.
2. Enter the **Name**, **Code** (uppercase, e.g., `LOGISTICS_LEAD`), and **Description**.
3. Save the role.
4. On the role detail page, assign permissions to this role.

**Viewing Permissions:** Navigate to **Users & Access > Permissions** (`/accounts/permissions/`). Permissions control specific actions (e.g., `can_approve_work_orders`, `can_post_grn`).

### 4.5 Database Backup

**When:** Before making major changes, before deployments, and as a regular daily practice.

1. Open a terminal or command prompt on the server.
2. Navigate to the project folder: `D:\PycharmProjects\floor_management_system-D3`
3. Run the backup command: `./hv`
4. The backup file is saved to the `backups/` folder with a timestamp.

**To restore from backup:**
Run `./hv restore` and select the backup file to restore.

**To list available backups:**
Run `./hv list`.

### 4.6 Running Seed Commands (Initial Data Setup)

Seed commands populate the system with essential reference data. Run them in this order for a fresh installation:

1. Activate the virtual environment: `venv\Scripts\activate`
2. Run seeds in order:
   - `python manage.py seed_bit_sizes`
   - `python manage.py seed_hdbs_types`
   - `python manage.py seed_smi_types`
   - `python manage.py seed_accounts --confirm`
   - `python manage.py seed_variant_cases`
   - `python manage.py seed_router_steps --confirm`
   - `python manage.py seed_roles_permissions`

**Important:** `seed_bit_sizes` must run before `seed_smi_types` and `seed_hdbs_types`. Always use the `--confirm` flag where required, otherwise the command runs in dry-run mode.

### 4.7 Health Check

Run `./hc` from the project folder. This script:
- Checks for unapplied database migrations
- Runs seed commands if needed
- Displays the current git status

---

## 5. Forms & Data Entry Reference

| Form / Page | Location | Required Fields | Notes |
|-------------|----------|-----------------|-------|
| Create User | Users & Access > Users > Create | Username, Password, First Name, Last Name | Email recommended but not required |
| Edit User | Users & Access > Users > (user) > Edit | Same as above | Cannot change username after creation |
| Create Role | Users & Access > Roles > Create | Name, Code | Code must be unique, uppercase |
| Create Permission | Users & Access > Permissions > Create | Name, Code | Code must be unique |
| Manage User Roles | Users & Access > Users > (user) > Manage Roles | Select at least one role | Multiple roles can be assigned |

---

## 6. Reports Available to You

| Report | Location | Description |
|--------|----------|-------------|
| User List | Users & Access > Users | All users with status, department, roles. Filterable and searchable. |
| Role List | Users & Access > Roles | All roles with user counts. |
| Audit Log | Notifications > Audit | System-wide audit trail of user actions. |
| Competency Matrix | HR & Admin > Competency Matrix | Employee-to-process authorization grid. |
| Training Gaps | HR & Admin > Training Gaps | Processes with insufficient certified operators. |

---

## 7. Notifications & Alerts

**What you receive:**
- Password reset requests from users (if email is configured)
- System error alerts (if workflow engine is enabled)

**What you trigger:**
- When you deactivate a user account, their active sessions are not terminated immediately; they expire after 24 hours.
- When you change a user's roles, the change takes effect on their next page load.

**Notification Bell:** The bell icon in the top navigation shows your unread count. Click it to see recent notifications. The count updates automatically every 10 seconds.

---

## 8. Approvals & Sign-offs

System Administrators do not have a formal approval workflow within the system. However, you may be asked to:

- **Approve role changes** requested by department managers (communicated verbally or via email; no in-system approval flow for this).
- **Verify data integrity** after seed commands or imports before handing off to the operations team.
- **Confirm backups** are completed before major system changes.

All user creation and role assignment actions are recorded in the audit log for traceability.

---

## 9. Frequently Asked Questions

**Q1: A user says they cannot see the Production Planner page. What should I check?**
A: Go to their user detail page and verify they have the PLANNER or OPS_MANAGER role assigned. The Production Planner is only visible to users with the appropriate role.

**Q2: Can I delete a user account?**
A: Yes, via Users & Access > Users > (user) > Delete. However, it is recommended to **deactivate** the account instead (uncheck "Is Active") to preserve the audit trail.

**Q3: The system shows "X unapplied migrations" when the server starts. What do I do?**
A: Run `venv\Scripts\python.exe manage.py migrate` from the project folder, then restart the server.

**Q4: How do I restart the server?**
A: Open Task Manager, end all Python processes, then run: `venv\Scripts\python.exe manage.py runserver 0.0.0.0:8001` from the project folder.

**Q5: A user forgot their password and cannot log in. What is the quickest fix?**
A: Navigate to Users & Access > Users > (user) > Reset Password. Set a temporary password (e.g., `Ardt@2025`) and tell the user to change it after login.

**Q6: Can I export the user list?**
A: Currently, user data can be exported via the Django Admin panel at `/admin/accounts/user/`. Select users and use the "Export" action. [NEEDS VERIFICATION]

**Q7: What happens if I accidentally delete a role that has users assigned?**
A: The system will prevent deletion if users are still assigned to the role. You must remove all user-role assignments first.

**Q8: How do I access the Django Admin panel?**
A: Navigate to `http://localhost:8001/admin/`. You must have superuser or staff status on your account. If you do not, another admin can grant it via the Django Admin.

---

## 10. Glossary

| Term | Definition |
|------|-----------|
| **Role** | A named set of capabilities assigned to a user (e.g., OPERATOR, QC_INSPECTOR). A user can have multiple roles. |
| **Permission** | A specific action a user is allowed to perform (e.g., "can_approve_work_orders"). Permissions are assigned to Roles, not directly to users. |
| **Seed Command** | A script that populates the database with initial reference data (bit sizes, account types, router steps, etc.). |
| **Migration** | A database structure change that must be applied when the system is updated. |
| **Django Admin** | A built-in administrative interface at `/admin/` that provides direct access to all database tables. |
| **Session** | A login session lasts 24 hours. After that, the user must log in again. |
| **Business Unit (Account)** | An organizational category (e.g., LSTK, ARAMCO, Halliburton) that drives work order numbering and routing. |
| **Backup** | A copy of the database file (`db.sqlite3`) saved with a timestamp in the `backups/` folder. |
| **venv** | The Python virtual environment containing all software dependencies. Always activate it before running commands. |
| **Health Check (hc)** | A script that verifies the system is in a good state: migrations applied, seeds run, git status clean. |
