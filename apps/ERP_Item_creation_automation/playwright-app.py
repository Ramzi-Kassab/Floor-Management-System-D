import os
import json
import glob
import time
import openpyxl
import pandas as pd

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from datetime import datetime
from excel_handler import find_excel_file, list_sheets, read_sheet, write_to_excel


# --------------------------------------------------------------------------------
# APP SETUP
# --------------------------------------------------------------------------------
app = Flask(__name__, template_folder='templates2')
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'change-me-please')
app.config['PORT'] = 5003
socketio = SocketIO(app, async_mode='eventlet')  # eventlet is easiest for dev
from excel_handler import bp as excel_bp
app.register_blueprint(excel_bp)   # add this once after `app = Flask(...)`
# Folder for storing workflow JSON files
WORKFLOWS_DIR = "workflows"
if not os.path.exists(WORKFLOWS_DIR):
    os.makedirs(WORKFLOWS_DIR)

CONFIG_FILE = "config.json"

# --------------------------------------------------------------------------------
# 1) HELPER: LOAD CONFIG (default URL, etc.)
# --------------------------------------------------------------------------------
def load_config():
    """Loads config.json or returns empty dict if not found."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

# --------------------------------------------------------------------------------
# 2) HELPER: EXCEL HANDLER (merged from excel_handler.py)
# --------------------------------------------------------------------------------
def find_excel_file(partial_name, folder_path):
    """Find Excel files that match a partial name in a specific folder."""
    pattern_xlsx = os.path.join(folder_path, f"*{partial_name}*.xlsx")
    pattern_xls = os.path.join(folder_path, f"*{partial_name}*.xls")
    matches = glob.glob(pattern_xlsx) + glob.glob(pattern_xls)
    return matches[0] if matches else None

def get_sheets(file_path):
    """Return a list of sheet names from an Excel file."""
    wb = openpyxl.load_workbook(file_path, read_only=True)
    return wb.sheetnames

def read_sheet(file_path, sheet_name):
    import pandas as pd
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)
    last_rows = df.tail(10)
    column_order = list(df.columns)

    records_with_row_numbers = []
    for idx, row in last_rows.iterrows():
        record = {'__excel_row__': idx + 2}  # Excel row = index + 2
        for col in column_order:
            record[col] = row.get(col, None)
        records_with_row_numbers.append(record)

    return records_with_row_numbers, column_order


def normalize_account_name(name):
    """Standardize various forms of account names to a canonical key."""
    if not name:
        return ''
    n = name.upper().replace('_', ' ').replace('-', ' ').replace('.', ' ')
    n = " ".join(n.split())  # Collapse whitespace
    tokens = set(n.split())
    if {'RC', 'LSTK'} <= tokens:
        return 'RC-LSTK'
    if {'LSTK', 'RC'} <= tokens:
        return 'RC-LSTK'
    # Add more if you have more account types!
    return n.replace(' ', '-')


# --------------------------------------------------------------------------------
# 3) HELPER: PLAYWRIGHT LOGIC (merged from web_handler.py)
# --------------------------------------------------------------------------------
def start_browser(url=None, headless=False, timeout=60000):
    """Launch a non-headless browser and optionally navigate to 'url'."""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    page.goto("about:blank", wait_until="domcontentloaded")
    if url:
        # If user typed something like "google.com", we add "https://"
        if not url.startswith("http"):
            url = "https://" + url
        resp = page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        if resp and not resp.ok:
            print(f"Warning: Status {resp.status} while loading {url}")
    return {
        'playwright': playwright,
        'browser': browser,
        'context': context,
        'page': page
    }

def close_browser(browser_data):
    """Close the given browser data dict safely."""
    try:
        page = browser_data['page']
        context = browser_data['context']
        browser = browser_data['browser']
        p = browser_data['playwright']
        page.close()
        context.close()
        browser.close()
        p.stop()
        return True
    except Exception as e:
        print(f"Error closing browser: {e}")
        return False

# Basic locators logic
def get_locator(page, locator_name, locators):
    if locator_name not in locators:
        raise ValueError(f"Locator '{locator_name}' not found")
    info = locators[locator_name]
    ltype = info['type']
    val = info['value']

    if ltype == 'xpath':
        return page.locator(f"xpath={val}")
    elif ltype == 'css':
        return page.locator(f"css={val}")
    elif ltype == 'id':
        return page.locator(f"id={val}")
    elif ltype == 'text':
        return page.get_by_text(val)
    else:
        raise ValueError(f"Unsupported locator type '{ltype}'")

def execute_action(page, action_dict, locators):
    """Interprets a dictionary to decide if we fill or click a locator."""

    locator_name = action_dict.get('locator')
    if not locator_name:
        return {'success': False, 'message': 'No locator in dict'}

    option_val = action_dict.get('option', '')
    clear_opt = action_dict.get('clear_option', False)
    delay_sec = float(action_dict.get('delay', 1))
    sleep_sec = float(action_dict.get('sleep1', 1))
    max_retries = int(action_dict.get('max_retries', 3))

    # Build the locator
    try:
        loc = get_locator(page, locator_name, locators)
    except Exception as e:
        return {'success': False, 'message': str(e)}

    # Retry logic
    for attempt in range(max_retries):
        try:
            loc.wait_for(state='visible', timeout=30000)
            if option_val.strip():
                # Fill
                if clear_opt:
                    loc.fill("", timeout=30000)
                loc.fill(option_val, timeout=30000)
            else:
                # Click
                loc.click(timeout=30000)
            time.sleep(sleep_sec)
            return {'success': True, 'message': f"Action success on '{locator_name}'"}
        except Exception as e:
            print(f"[Attempt {attempt+1}] Error: {e}")
            time.sleep(delay_sec)

    return {'success': False, 'message': f"Failed after {max_retries} tries on '{locator_name}'"}

# --------------------------------------------------------------------------------
# 4) LOAD LOCATORS & DICTIONARIES from JSON
# --------------------------------------------------------------------------------
def load_locators():
    with open('locators.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def load_dictionaries():
    with open('dictionaries.json', 'r', encoding='utf-8') as f:
        return json.load(f)

locators = load_locators()
dictionaries = load_dictionaries()
browser_instance = None

# --------------------------------------------------------------------------------
# 5) WORKFLOWS: Each workflow stored in /workflows/<name>.json
# --------------------------------------------------------------------------------
def list_workflow_files():
    """Return a list of workflow objects: each has 'workflow_name', 'steps'."""
    results = []
    for f in os.listdir(WORKFLOWS_DIR):
        if f.endswith(".json"):
            path = os.path.join(WORKFLOWS_DIR, f)
            with open(path, 'r', encoding='utf-8') as wf:
                data = json.load(wf)
                results.append(data)
    return results

def load_workflow(workflow_name):
    path = os.path.join(WORKFLOWS_DIR, f"{workflow_name}.json")
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_workflow(workflow_name, steps_list):
    data = {
        "workflow_name": workflow_name,
        "steps": steps_list
    }
    path = os.path.join(WORKFLOWS_DIR, f"{workflow_name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def delete_workflow(workflow_name):
    path = os.path.join(WORKFLOWS_DIR, f"{workflow_name}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

@app.route('/get_workflow/<workflow_name>')
def get_workflow_route(workflow_name):
    """Return a workflow's JSON, for editing in the front-end."""
    wf_data = load_workflow(workflow_name)
    if not wf_data:
        return jsonify({"error": f"Workflow '{workflow_name}' not found"}), 404
    return jsonify(wf_data)

# --------------------------------------------------------------------------------
# FLASK ROUTES
# --------------------------------------------------------------------------------

@app.route('/')
def index():
    """Home page with navigation links."""
    return render_template('index.html')

# -----------------------------
# LOCATORS management
# -----------------------------
@app.route('/locators', methods=['GET', 'POST'])
def locators_route():
    global locators
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            locator_name = request.form.get('locator_name')
            locator_value = request.form.get('locator_value')
            locator_type = request.form.get('locator_type')
            locators[locator_name] = {
                'type': locator_type,
                'value': locator_value
            }
            # Save to locators.json
            with open('locators.json', 'w', encoding='utf-8') as f:
                json.dump(locators, f, indent=2)
            return redirect(url_for('locators_route'))

        elif action == 'delete':
            locator_name = request.form.get('locator_name')
            if locator_name in locators:
                del locators[locator_name]
                with open('locators.json', 'w', encoding='utf-8') as f:
                    json.dump(locators, f, indent=2)
            return redirect(url_for('locators_route'))
    return render_template('locators.html', locators=locators)

# -----------------------------
# DICTIONARIES management
# -----------------------------
@app.route('/dictionaries', methods=['GET', 'POST'])
def dictionaries_route():
    global dictionaries
    global locators

    error = None
    edit_mode = False
    edit_name = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save':
            dict_name = request.form.get('dict_name')
            dict_content = request.form.get('dict_content')
            try:
                new_dict = json.loads(dict_content)
                dictionaries[dict_name] = new_dict
                with open('dictionaries.json', 'w', encoding='utf-8') as f:
                    json.dump(dictionaries, f, indent=2)
                return redirect(url_for('dictionaries_route'))
            except json.JSONDecodeError as e:
                error = f"Invalid JSON: {e}"

        elif action == 'update':
            dict_name = request.form.get('dict_name')
            dict_content = request.form.get('dict_content')
            if dict_name in dictionaries:
                try:
                    new_dict = json.loads(dict_content)
                    dictionaries[dict_name] = new_dict
                    with open('dictionaries.json', 'w', encoding='utf-8') as f:
                        json.dump(dictionaries, f, indent=2)
                    return redirect(url_for('dictionaries_route'))
                except json.JSONDecodeError as e:
                    error = f"Invalid JSON: {e}"
                    edit_mode = True
                    edit_name = dict_name

        elif action == 'delete':
            dict_name = request.form.get('dict_name')
            if dict_name in dictionaries:
                del dictionaries[dict_name]
                with open('dictionaries.json', 'w', encoding='utf-8') as f:
                    json.dump(dictionaries, f, indent=2)
            return redirect(url_for('dictionaries_route'))

        elif action == 'edit':
            # You could use GET for edit, but if POST, just flag edit mode and let frontend handle it
            edit_mode = True
            edit_name = request.form.get('dict_name')

    # Always load these for rendering the template
    with open('./locators.json') as f:
        all_locators = json.load(f)
    locator_names = list(all_locators.keys())
    last_column_order = session.get('last_column_order', [])

    return render_template(
        'dictionaries.html',
        dictionaries=dictionaries,
        error=error,
        edit_mode=edit_mode,
        edit_name=edit_name,
        locator_names=locator_names,
        last_column_order=last_column_order,
    )



@app.route('/get_dictionary/<dict_name>')
def get_dictionary_route(dict_name):
    # Load the entire dictionaries.json
    try:
        with open('dictionaries.json', 'r', encoding='utf-8') as f:
            all_dictionaries = json.load(f)

        # Check if dict_name is a key
        if dict_name in all_dictionaries:
            return jsonify(all_dictionaries[dict_name])  # Return the dictionary as JSON
        else:
            # Key not found, return 404
            return jsonify({"error": f"Dictionary '{dict_name}' not found"}), 404

    except Exception as e:
        # If any other error, return 500 with message
        return jsonify({"error": str(e)}), 500


import re


def fill_placeholders(template_str, row, context):
    """Replace {{KEY}} with value from row (or context)."""
    if not isinstance(template_str, str):
        return template_str  # Only handle strings
    def replacer(match):
        key = match.group(1).strip()
        if key in row:
            return str(row[key])
        if key in context:
            return str(context[key])
        return ""
    return re.sub(r'{{(.*?)}}', replacer, template_str)


# -----------------------------
# EXCEL handler
# -----------------------------


def load_config():
    with open("config.json", "r") as f:
        return json.load(f)


# -----------------------------
# WORKFLOWS
# -----------------------------
@app.route('/workflows', methods=['GET', 'POST'])
def workflows_route():
    """
    Handles all actions for workflows:
      - create: create a new workflow (action=create)
      - execute: execute an existing workflow (action=execute)
      - delete_workflow: remove a workflow file (action=delete_workflow)
      - update_workflow: edit an existing workflow (action=update_workflow)
    """
    global browser_instance  # or however you track your browser instance
    print("2 All selected data:", session.get('all_selected_data'))
    print("2 All selected data:", session.get('all_selected_data'))
    selected_by_sheet = session.get('selected_rows_by_sheet', {}) or {}

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            # Create a new workflow from user input
            workflow_name = request.form.get('workflow_name')
            steps = request.form.getlist('workflow_steps')
            valid_sheets = request.form.getlist('valid_sheets')
            data = {
                "workflow_name": workflow_name,
                "steps": steps,
                "valid_sheets": valid_sheets
            }
            path = os.path.join(WORKFLOWS_DIR, f"{workflow_name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return redirect(url_for('workflows_route'))


        elif action == 'execute':

            workflow_name = request.form.get('workflow_name')

            # Load the workflow so we can validate against its valid sheets.

            wf_path = os.path.join(WORKFLOWS_DIR, f"{workflow_name}.json")

            if not os.path.isfile(wf_path):
                flash(f"Workflow '{workflow_name}' not found.", "danger")

                return redirect(url_for('workflows_route'))

            with open(wf_path, 'r', encoding='utf-8') as f:

                wf = json.load(f)

            valid_sheets = set(wf.get('valid_sheets', []))

            # intersect selected sheets with workflow's valid sheets

            selected_valid = {sh: rows for sh, rows in (selected_by_sheet or {}).items() if sh in valid_sheets}

            # guard rails: no rows selected for this workflow

            if not selected_valid or sum(len(v) for v in selected_valid.values()) == 0:
                flash("Cannot execute: no valid Excel rows selected for this workflow.", "warning")

                return redirect(url_for('workflows_route'))

            # keep a lightweight snapshot for the results page (don’t bloat session)

            session['last_execution'] = {

                "workflow_name": workflow_name,

                "selected": {

                    sh: [r.get('__excel_row__') for r in rows] for sh, rows in selected_valid.items()

                },

                "headers": session.get('last_column_order', [])

            }

            # Redirect – results route will pull from session['last_execution']

            return redirect(url_for('workflow_results', workflow_name=workflow_name))


        elif action == 'delete_workflow':
            # Remove a workflow file from /workflows
            workflow_name = request.form.get('workflow_name')
            delete_workflow(workflow_name)
            return redirect(url_for('workflows_route'))

        elif action == 'update_workflow':
            """
            The user edited an existing workflow:
              - old_workflow_name: the original file name
              - new_workflow_name: the (possibly changed) new name
              - workflow_steps: updated steps list
              - valid_sheets: updated list of valid sheets
            If the name changed, we remove the old file and create the new one.
            """
            old_name = request.form.get('old_workflow_name')
            new_name = request.form.get('new_workflow_name')
            steps = request.form.getlist('workflow_steps')
            valid_sheets = request.form.getlist('valid_sheets')

            data = {
                "workflow_name": new_name,
                "steps": steps,
                "valid_sheets": valid_sheets
            }

            if old_name != new_name:
                delete_workflow(old_name)
            path = os.path.join(WORKFLOWS_DIR, f"{new_name}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            return redirect(url_for('workflows_route'))

        # If action is unrecognized, just redirect back
        return redirect(url_for('workflows_route'))

    # GET request -> list all workflow files
    all_workflows = list_workflow_files()
    config = load_config()
    default_url = config.get('default_url', '')
    return render_template('workflows.html',
                           workflows=all_workflows,
                           dictionaries=dictionaries,
                           default_url=default_url)


@socketio.on('run_workflow')
def run_workflow_socketio(data):
    global browser_instance
    workflow_name = data.get('workflow_name', '')
    typed_url = data.get('workflow_url', '').strip() if data.get('workflow_url') else ''

    emit('workflow_update', {'step': 'INIT', 'success': True, 'message': 'Handler started!'})

    wf_data = load_workflow(workflow_name)
    if not wf_data:
        emit('workflow_update', {'step': 'INIT', 'success': False, 'message': f"Workflow \"{workflow_name}\" not found"})
        emit('workflow_done', {'status': 'done'})
        return

    # Optionally close existing browser
    if browser_instance:
        close_browser(browser_instance)
        browser_instance = None

    config = load_config()
    default_url = config.get('default_url', '')
    url_to_open = typed_url if typed_url else default_url

    # Start new browser
    browser_instance = start_browser(url_to_open)
    assert isinstance(browser_instance, dict) and 'page' in browser_instance
    page = browser_instance['page']


    selected_rows = session.get('all_selected_data', [])
    for row in selected_rows:
        account = normalize_account_name(row.get('FROM', ''))
        context = {}

        if account == "RC-LSTK":
            item_number, _ = get_next_item_number("RC-LSTK")
            context['ITEM NO'] = item_number

        for step in wf_data['steps']:
            print("RAW STEP VALUE:", repr(step))
            # --- ensure dict_key is set before using it ---
            dict_key = None
            step_obj = None

            if isinstance(step, dict):
                step_obj = step
            else:
                try:
                    step_obj = json.loads(step)
                except Exception as e:
                    step_obj = None

            if step_obj and isinstance(step_obj, dict) and "locator_by_account" in step_obj:
                locator_map = step_obj["locator_by_account"]
                # Normalize account name, e.g., replace spaces
                acc_key = account.replace(" ", "-") if account else None
                dict_key = locator_map.get(acc_key, locator_map.get("default"))
                step_name_for_log = f"locator_by_account: {acc_key or ''} → {dict_key}"
                print("Trying account key:", acc_key, "Available:", list(locator_map.keys()))

            else:
                dict_key = step if isinstance(step, str) else None
                step_name_for_log = dict_key

            # --- skip if cannot resolve dict_key ---
            if not dict_key or dict_key not in dictionaries:
                emit('workflow_update', {
                    'step': str(step),
                    'success': False,
                    'message': f"Could not resolve dictionary key for step: {step}",
                    'account': account,
                    'serial': row.get('SERIAL NO')
                })
                socketio.sleep(0.1)
                continue

            # --- action dict and fill placeholders ---
            action_dict = dictionaries[dict_key].copy()
            for key in list(action_dict.keys()):
                val = action_dict[key]
                if isinstance(val, str):
                    action_dict[key] = fill_placeholders(val, row, context)

            locator_name = action_dict.get('locator')
            if 'locator_by_account' in action_dict:
                locator_name = action_dict['locator_by_account'].get(account, action_dict['locator_by_account'].get('default'))
            action_dict['locator'] = locator_name

            # --- action logic for RC-LSTK Product_number_Field_dict ---
            max_tries = 5
            success = False
            r = None  # Always define r
            if account == "RC-LSTK" and dict_key == "Product_number_Field_dict":
                counters = load_item_counters()
                num = counters.get("RC-LSTK", 1)
                max_tries = 100  # Try as many as you want!
                for attempt in range(max_tries):
                    item_number = f"RPR-RC-LST-{num:04d}"
                    action_dict['option'] = item_number
                    context['ITEM NO'] = item_number
                    print(f"[{attempt + 1}] Trying item_number={item_number}")

                    r = execute_action(page, action_dict, locators)
                    time.sleep(0.7)

                    if error_detected_duplicate_item(page):
                        print(f"[{attempt + 1}] Duplicate detected, closing warning and retrying...")
                        execute_action(page, dictionaries['Already_Assigned_Error_Message_Close_dict'], locators)
                        time.sleep(0.5)
                        num += 1  # Only increment in memory!
                        continue
                    else:
                        print(f"[{attempt + 1}] Success! No duplicate.")
                        # Only save the counter NOW!
                        counters["RC-LSTK"] = num + 1
                        save_item_counters(counters)
                        success = True
                        break
                else:
                    emit('workflow_update', {'step': dict_key, 'success': False,
                                             'message': "Couldn't find available item number after trying 100 options"})
                    continue

            else:
                r = execute_action(page, action_dict, locators)

            # --- Save for later if needed ---
            if 'save_as' in action_dict:
                context[action_dict['save_as']] = action_dict.get('option')

            emit('workflow_update', {
                'step': step_name_for_log,
                'success': r['success'],
                'message': r['message'],
                'account': account,
                'serial': row.get('SERIAL NO')
            })
            socketio.sleep(0.2)

    emit('workflow_done', {'status': 'done'})


def error_detected_duplicate_item(page):
    """
    Returns True if the duplicate item number warning is detected, otherwise False.
    """
    try:
        warning_text = "The number has already been assigned to a product. Specify a new number."
        # This selects ALL spans with class 'messageBar-message'
        spans = page.locator("span.messageBar-message")
        for i in range(spans.count()):
            if warning_text in spans.nth(i).inner_text():
                return True
        return False
    except Exception:
        return False



@app.route('/workflow_results')
def workflow_results():
    workflow_name = request.args.get('workflow_name', '')
    return render_template('workflow_results.html', workflow_name=workflow_name)


@app.route('/stop_browser', methods=['POST'])
def stop_browser_route():
    global browser_instance
    if browser_instance:
        close_browser(browser_instance)
        browser_instance = None
        return jsonify({"success": True, "message": "Browser closed."})
    return jsonify({"success": False, "message": "No browser running."})


ITEM_COUNTER_FILE = 'item_counters.json'


def load_item_counters():
    if not os.path.exists(ITEM_COUNTER_FILE):
        return {}
    with open(ITEM_COUNTER_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_item_counters(counters):
    with open(ITEM_COUNTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(counters, f, indent=2)


def get_next_item_number(account, prefix='RPR-RC-LST-', start=1):
    counters = load_item_counters()
    num = counters.get(account, start)
    item_number = f"{prefix}{num:04d}"  # e.g. RPR-RC-LST-0096
    counters[account] = num + 1
    save_item_counters(counters)
    return item_number, num

def get_next_available_item_number(account, prefix='RPR-RC-LST-', start=1):
    counters = load_item_counters()
    num = counters.get(account, start)
    while True:
        item_number = f"{prefix}{num:04d}"
        # (Insert a check here if item_number is already assigned in your DB, if possible)
        yield item_number, num  # Return candidate, don't increment saved counter yet
        num += 1



# --------------------------------------------------------------------------------
# RUN
# --------------------------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True, port=5003)
