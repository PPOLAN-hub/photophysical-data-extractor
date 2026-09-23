#!/usr/bin/env python3
"""Compare two compact PDE regression signatures without normalizing values."""

import json
import sys
from pathlib import Path


def differences(left, right, path="$", output=None):
    output = output if output is not None else []
    if type(left) is not type(right):
        output.append({"path": path, "baseline": left, "candidate": right, "reason": "type"})
        return output
    if isinstance(left, dict):
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left:
                output.append({"path": child, "baseline": "<missing>", "candidate": right[key], "reason": "added"})
            elif key not in right:
                output.append({"path": child, "baseline": left[key], "candidate": "<missing>", "reason": "removed"})
            else:
                differences(left[key], right[key], child, output)
    elif isinstance(left, list):
        if len(left) != len(right):
            output.append({"path": path, "baseline": len(left), "candidate": len(right), "reason": "length"})
        for index, (a, b) in enumerate(zip(left, right)):
            differences(a, b, f"{path}[{index}]", output)
    elif left != right:
        output.append({"path": path, "baseline": left, "candidate": right, "reason": "value"})
    return output


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: compare_regression.py BASELINE.json CANDIDATE.json")
    baseline = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    candidate = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    found = differences(baseline, candidate)
    payload = {"status": "identical" if not found else "different", "difference_count": len(found), "differences": found}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not found else 1)


if __name__ == "__main__":
    main()
