"""Utilities to parse a lightweight structured text format into CSV strings.

The parser accepts a simple, indented, YAML-like text format that supports:
- primitive key: value pairs on a single line
- objects defined by a header line ending with a colon and an indented block
- arrays with a header specifying a count and a braced list of column names

Each detected structure is converted to a CSV string (headers + rows) and
returned in a dictionary keyed by the hierarchical path (dot-separated for
nested objects).

The module exposes a single high-level function `parse_to_csv` and several
internal helpers used during scanning.
"""

import re
from typing import List, Dict


def get_csv_key_value(line: str):
    """Parse a single-line key:value pair and return a CSV-like tuple.

    The function matches lines like "name: value" but intentionally excludes
    lines where the value begins with a '[' (these are handled as arrays).

    Args:
        line: A single input text line (leading/trailing whitespace should be
              stripped by the caller).

    Returns:
        None if the line does not match a primitive key:value pair.
        Otherwise returns a tuple of the form:
            (key, csv_text, [key], [value], None)
        where `csv_text` contains a minimal CSV representation (header on the
        first line and the value on the second line) and the final element is
        None for compatibility with other helper return signatures.
    """
    if not (m := re.match(r"^(?P<key>\w+)\s*:\s*(?P<value>(?!\[).+)$", line)):
        return None

    key = m.group("key")
    value = m.group("value")

    return key, f"{key}\n{value}\n", [key], [value], None


def get_csv_array(lines: List[str], start_index: int):
    """Parse an array block starting at `start_index`.

    Expected header format (single line), followed by `count` data lines:
        listName [N] {col1, col2, ...}:
            value-row-1
            value-row-2
    The header may optionally end with a colon. The following `count` lines
    are considered array rows (they are not parsed into sub-columns by this
    helper; they are taken verbatim and stripped).

    Args:
        lines: Full list of input lines.
        start_index: Index where the array header is expected.

    Returns:
        None if the line at `start_index` does not match an array header.
        Otherwise returns a tuple:
            (name, csv_text, columns, values, end_index)
        where `csv_text` is columns + rows separated by newlines and `end_index`
        is the index of the last line consumed for this array (inclusive).
    """
    # Support two header syntaxes:
    # 1) name [N] {col1, col2}:
    # 2) name [N]:  (no braces, items follow as dash-prefixed blocks or bracketed keys)
    pattern_braced = r"^\s*([^\[\]\{\}:]+?)\s*\[\s*(\d+)\s*\]\s*\{\s*([^}]*)\}\s*:?\s*$"
    pattern_simple = r"^\s*([^\[\]\{\}:]+?)\s*\[\s*(\d+)\s*\]\s*:?\s*$"

    line = lines[start_index]

    m = re.match(pattern_braced, line)
    columns = []
    values: List[str] = []

    if m:
        name = m.group(1).strip()
        count = int(m.group(2))
        columns = [c.strip() for c in m.group(3).split(",") if c.strip()]
        values = [
            lines[i].strip()
            for i in range(start_index + 1, min(len(lines), start_index + 1 + count))
        ]
        csv_lines = []
        if columns:
            csv_lines.append(",".join(columns))
            csv_lines += values
        csv = "\n".join(csv_lines) + ("\n" if csv_lines else "")
        end = min(len(lines) - 1, start_index + count)
        return name, csv, columns, values, end

    m = re.match(pattern_simple, line)
    if not m:
        return None

    name = m.group(1).strip()
    count = int(m.group(2))

    # Parse the following `count` items. Items may be:
    # - dash-prefixed object blocks starting with a line like "  - id: 1" and
    #   followed by indented primitive key: value lines.
    # - single-line bracketed-key entries like "  - [2]: 1,2"
    # We'll collect values as CSV rows. If bracketed keys are present we'll
    # treat them as comma-separated cells; if object items are present we'll
    # collect primitive fields into columns (union across items) and then
    # produce header + rows.

    items = []
    i = start_index + 1
    consumed = 0
    while i < len(lines) and consumed < count:
        raw = lines[i]
        stripped = raw.lstrip()
        # detect dash-prefixed line
        if stripped.startswith("- ") or stripped == "-":
            # start of an item
            # if line is like "- key: val" then it's an inline primitive
            after_dash = stripped[1:].lstrip()
            if after_dash:
                # could be bracketed key or inline kv
                # bracketed key pattern: [number]: val
                bm = re.match(r"^\[(?P<k>[^\]]+)\]\s*:\s*(?P<v>.*)$", after_dash)
                if bm:
                    items.append({bm.group("k"): bm.group("v").strip()})
                    i += 1
                    consumed += 1
                    continue
                # inline kv like "id: 1"
                ikv = re.match(r"^(?P<k>\w+)\s*:\s*(?P<v>.*)$", after_dash)
                if ikv:
                    obj = {ikv.group("k"): ikv.group("v").strip()}
                    # collect following indented lines that belong to this item
                    j = i + 1
                    while j < len(lines):
                        # stop when next top-level list item or blank line encountered
                        if re.match(r"^\s*-\s", lines[j]) or re.match(r"^\S", lines[j]):
                            break
                        line_j = lines[j].strip()
                        kv = re.match(r"^(?P<k>\w+)\s*:\s*(?P<v>.*)$", line_j)
                        if kv:
                            obj[kv.group("k")] = kv.group("v").strip()
                        j += 1
                    items.append(obj)
                    # advance to j (next item)
                    i = j
                    consumed += 1
                    continue
            # case of a dash-only line or dash followed by nested block
            # gather the block indentation to capture nested primitives
            indent_match = re.match(r"^(?P<indent>\s*)-\s*$", raw)
            base_indent = len(indent_match.group("indent")) if indent_match else len(raw) - len(stripped)
            obj = {}
            j = i + 1
            while j < len(lines):
                line_j = lines[j]
                leading = re.match(r"^(\s*)", line_j).group(1)
                if len(leading) <= base_indent:
                    break
                line_str = line_j.strip()
                kv = re.match(r"^(?P<k>\w+)\s*:\s*(?P<v>.*)$", line_str)
                if kv:
                    obj[kv.group("k")] = kv.group("v").strip()
                j += 1
            items.append(obj)
            i = j
            consumed += 1
            continue

        # also support bracketed items without leading dash (less common)
        bm = re.match(r"^\s*\[([^\]]+)\]\s*:\s*(.*)$", raw)
        if bm:
            items.append({bm.group(1): bm.group(2).strip()})
            i += 1
            consumed += 1
            continue

        # fallback: treat the stripped line as a simple value row
        items.append({"value": stripped})
        i += 1
        consumed += 1

    # Determine CSV output
    # If items are simple single-key maps with bracketed numeric keys, output rows
    # with their values (no header). If items are objects with multiple keys,
    # unify columns and output header + rows.
    all_keys = []
    for it in items:
        for k in it.keys():
            if k not in all_keys:
                all_keys.append(k)

    csv_lines: List[str] = []
    if len(all_keys) == 1 and all_keys[0] == "value":
        # simple rows
        csv_lines = [v.get("value", "") for v in items]
    elif len(all_keys) == 1:
        # single column with different key name (e.g., '[2]')
        csv_lines = [it.get(all_keys[0], "") for it in items]
    else:
        # multi-column: header from all_keys and values rows in that order
        csv_lines.append(",".join(all_keys))
        for it in items:
            row = [it.get(k, "") for k in all_keys]
            csv_lines.append(",".join(row))

    csv = "\n".join(csv_lines) + ("\n" if csv_lines else "")
    end = i - 1 if i > start_index else start_index

    return name, csv, all_keys, [""] * len(items), end


def get_csv_object(lines: List[str], start_index: int):
    """Parse an indented object block starting at `start_index`.

    An object header is a line ending with a colon whose following indented
    block contains primitive key:value pairs, and optionally nested objects or
    arrays. This helper collects primitive pairs in the immediate block and
    returns them as a single CSV (header row + value row). Nested objects and
    arrays are detected but not expanded by this function (their processing is
    handled at a higher level).

    Args:
        lines: Full list of input lines.
        start_index: Index where the object header is expected.

    Returns:
        None if the line at `start_index` is not an object header.
        Otherwise returns a tuple:
            (name, csv_text, columns, values, end_index)
        where `csv_text` contains a CSV with collected primitive keys/values
        from the object's immediate block and `end_index` is the index of the
        last line in the object's block (inclusive).
    """
    header_m = re.match(r"^(?P<indent>\s*)(?P<key>\w+)\s*:\s*$", lines[start_index])

    if not header_m:
        return None

    start_indent = len(header_m.group("indent"))
    name = header_m.group("key")
    columns: List[str] = []
    values: List[str] = []

    i = start_index + 1
    while i < len(lines):
        line = lines[i]

        if not line:
            i += 1
            continue

        leading = re.match(r"^(\s*)", line).group(1)
        indent = len(leading)

        if indent <= start_indent:
            break

        stripped = line.strip()
        kv = get_csv_key_value(stripped)

        if kv:
            _, _, kcols, kvals, _ = kv
            columns += kcols
            values += kvals
            i += 1
            continue

        if re.match(r"^\s*\w+\s*:\s*$", line):
            nested = get_csv_object(lines, i)
            if nested:
                _, _, _, _, end_idx = nested
                i = len(lines) if end_idx is None else end_idx + 1
                continue

        arr = get_csv_array(lines, i)

        if arr:
            _, _, _, _, end_idx = arr
            i = len(lines) if end_idx is None else end_idx + 1
            continue

        i += 1
    csv = ",".join(columns) + "\n" if columns else ""

    if columns:
        csv += ",".join(values) + "\n"

    return name, csv, columns, values, i - 1


def parse_to_csv(encoded: str) -> Dict[str, str]:
    """
    Parse encoded string data into CSV format and return a dictionary of CSV strings.
    This function processes multi-line encoded text containing structured data (objects, arrays,
    and key-value pairs) and converts them into CSV format. Each distinct data structure is
    stored as a separate CSV string in the returned dictionary, keyed by its hierarchical path.
    Args:
        encoded (str): A multi-line string containing structured data with objects, arrays,
                       and primitive key-value pairs. The structure should follow a specific
                       format where objects and arrays can be nested.
    Returns:
        Dict[str, str]: A dictionary where:
            - Keys are dot-separated paths representing the hierarchical structure
              (e.g., "parent.child", "array_name")
            - Values are CSV-formatted strings with headers and data rows
    The function handles:
        - Simple key-value pairs (converted to single-column CSVs)
        - Nested objects (extracted and stored with dot-notation paths)
        - Arrays (converted to multi-row CSVs)
        - Primitive values within blocks (aggregated into CSV format)
    Example:
        >>> encoded_data = "user:\\n  name: John\\n  age: 30"
        >>> result = parse_to_csv(encoded_data)
        >>> # Returns: {"user": "name,age\\nJohn,30\\n", ...}
    """
    lines = encoded.splitlines()
    index = 0
    csvs: Dict[str, str] = {}

    def extract_primitives_from_block(start, end):
        cols: List[str] = []
        vals: List[str] = []

        i = start
        while i <= end and i < len(lines):
            stripped = lines[i].strip()
            kv = get_csv_key_value(stripped)

            if kv:
                _, _, kcols, kvals, _ = kv
                cols += kcols
                vals += kvals

            i += 1
        if cols:
            return ",".join(cols) + "\n" + ",".join(vals) + "\n"

        return ""

    def scan_block_for_nested(start, end, parent_path):
        i = start

        while i <= end and i < len(lines):
            nested = get_csv_object(lines, i)
            if nested:
                n_name, n_csv, _, _, n_end = nested
                full_name = f"{parent_path}.{n_name}" if parent_path else n_name

                if not n_csv:
                    n_csv = extract_primitives_from_block(i + 1, n_end)

                csvs[full_name] = n_csv

                if n_end and n_end >= i + 1:
                    scan_block_for_nested(i + 1, n_end, full_name)

                i = (n_end + 1) if n_end is not None else i + 1

                continue

            arr = get_csv_array(lines, i)

            if arr:
                a_name, a_csv, _, _, a_end = arr
                full_name = f"{parent_path}.{a_name}" if parent_path else a_name
                csvs[full_name] = a_csv
                i = (a_end + 1) if a_end is not None else i + 1

                continue

            i += 1

    while index < len(lines):
        line = lines[index]

        if m := re.match(r"^\s*(?P<key>\w+)\s*:\s*(?P<value>(?!\[).+)$", line):
            key = m.group("key")
            csvs[key] = f"{key}\n{m.group('value')}\n"
            index += 1
            continue

        obj = get_csv_object(lines, index)

        if obj:
            name, csv, _, _, end_idx = obj
            if not csv:
                csv = extract_primitives_from_block(index + 1, end_idx)
            csvs[name] = csv
            scan_block_for_nested(index + 1, end_idx, name)
            index = end_idx + 1 if end_idx is not None else index + 1
            continue

        arr = get_csv_array(lines, index)
        if arr:
            name, csv, _, _, end_idx = arr
            csvs[name] = csv
            index = end_idx + 1 if end_idx is not None else index + 1
            continue

        index += 1
    return csvs
