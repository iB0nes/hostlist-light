"""Lightweight implementation of hostlist API."""
import re


class BadHostlist(Exception):
    """Host list parameter format not accepted or mistaken."""


MAX_SIZE = 100000


def expand_hostlist(hostlist, allow_duplicates=False, sort=False):
    """Expand a hostlist expression into a list of host names."""
    results = []
    bracket_level = 0
    part = ""

    for c in hostlist + ",":
        if c == "," and bracket_level == 0:
            if part:
                results.extend(expand_part(part))
            part = ""
        else:
            part += c
        # Check for brackets
        if c == "[":
            bracket_level += 1
        elif c == "]":
            bracket_level -= 1
        # Validate format
        if bracket_level > 1:
            raise BadHostlist("nested brackets")
        if bracket_level < 0:
            raise BadHostlist("unbalanced brackets")

    if bracket_level > 0:
        raise BadHostlist("unbalanced brackets")

    if not allow_duplicates:
        results = remove_duplicates(results)
    if sort:
        results = sorted(results, key=numeric_sort_key)
    return results


def expand_part(s):
    """Expand a single hostlist part without top-level commas."""
    if s == "":
        return [""]

    m = re.match(r'([^,\[]*)(\[[^\]]*\])?(.*)', s)
    (prefix, rangelist, rest) = m.group(1, 2, 3)

    rest_expanded = expand_part(rest)

    if not rangelist:
        us_expanded = [prefix]
    else:
        us_expanded = expand_rangelist(prefix, rangelist[1:-1])

    if len(us_expanded) * len(rest_expanded) > MAX_SIZE:
        raise BadHostlist("results too large")

    return [us_part + rest_part
            for us_part in us_expanded
            for rest_part in rest_expanded]


def expand_rangelist(prefix, rangelist):
    """Expand a comma-separated numeric rangelist with prefix."""
    results = []
    for numeric_range in rangelist.split(","):
        results.extend(expand_range(prefix, numeric_range))
    return results


def expand_range(prefix, numeric_range):
    """Expand one numeric range token with prefix."""
    m = re.match(r'^[0-9]+$', numeric_range)
    if m:
        return [f"{prefix}{numeric_range}"]

    m = re.match(r'^([0-9]+)-([0-9]+)$', numeric_range)
    if not m:
        raise BadHostlist("bad range")

    (s_low, s_high) = m.group(1, 2)
    low = int(s_low)
    high = int(s_high)
    width = len(s_low)

    if high < low:
        raise BadHostlist("start > stop")
    elif high - low > MAX_SIZE:
        raise BadHostlist("range too large")

    results = []
    for i in range(low, high + 1):
        results.append(f"{prefix}{i:0{width}d}")
    return results


def remove_duplicates(l):
    """Remove duplicates while preserving original order."""
    seen = set()
    result = []
    for item in l:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def collect_hostlist(hosts, silently_discard_bad=False):
    """Collect host names into compressed hostlist expression."""
    # Clean up inputs
    cleaned = []
    for host in hosts:
        host = host.strip()
        if host:
            # Check for forbidden characters
            if '[' in host or ']' in host:
                if not silently_discard_bad:
                    raise BadHostlist("forbidden characters")
            else:
                cleaned.append(host)

    # Remove duplicates and sort
    cleaned = remove_duplicates(cleaned)
    cleaned = sorted(cleaned, key=numeric_sort_key)
    if not cleaned:
        return ""

    # Each entry is (unprocessed_left, processed_right)
    left_right = [(host, "") for host in cleaned]
    looping = True
    while looping:
        left_right, looping = collect_hostlist_1(left_right)
    return ",".join(right for _, right in left_right)


def collect_hostlist_1(left_right):
    """Peel the rightmost number off each left part and merge entries that
    differ only in that number. Returns (new_left_right, needs_another_pass)."""
    groups = {}
    for left, right in left_right:
        m = re.match(r'^(.*?)([0-9]+)([^0-9]*)$', left)
        if not m:
            groups.setdefault((None, left + right, 0), []).append(None)
            continue
        prefix, num, tail = m.groups()
        # Zero-padded numbers are only merged with the same width
        width = len(num) if num.startswith("0") else 0
        groups.setdefault((prefix, tail + right, width), []).append(int(num))

    left_right = []
    for (prefix, suffix, width), nums in groups.items():
        if prefix is None:
            left_right.append(("", suffix))
            continue
        nums = sorted(set(nums))
        runs = []
        start = prev = nums[0]
        for n in nums[1:]:
            if n != prev + 1:
                runs.append((start, prev))
                start = n
            prev = n
        runs.append((start, prev))
        range_str = ",".join(format_range(lo, hi, width) for lo, hi in runs)
        if len(nums) == 1:
            new_right = range_str + suffix
        else:
            new_right = "[" + range_str + "]" + suffix
        left_right.append((prefix, new_right))
    return left_right, any(left for left, _ in left_right)


def format_range(low, high, width):
    """Format inclusive numeric range using fixed width."""
    if low == high:
        return f"{low:0{width}d}"
    else:
        return f"{low:0{width}d}-{high:0{width}d}"


def numerically_sorted(l):
    """Sort host names with numeric-aware ordering."""
    return sorted(l, key=numeric_sort_key)


def numeric_sort_key(x):
    """Build alternating string/integer sort key (always starts with a string)."""
    return [int(part) if i % 2 else part
            for i, part in enumerate(re.split(r'([0-9]+)', x))]


def parse_slurm_tasks_per_node(s):
    """Parse SLURM_TASKS_PER_NODE syntax (e.g. "2(x3),1") into task counts."""
    result = []
    for part in s.split(","):
        m = re.match(r'^([0-9]+)(\(x([0-9]+)\))?$', part)
        if not m:
            raise BadHostlist("bad task list syntax")
        tasks = int(m.group(1))
        repetitions = int(m.group(3)) if m.group(3) else 1
        if len(result) + repetitions > MAX_SIZE:
            raise BadHostlist("task list too large")
        result.extend([tasks] * repetitions)
    return result
