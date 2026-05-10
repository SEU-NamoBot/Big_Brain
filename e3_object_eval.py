#!/usr/bin/env python3
"""
E3 object-semantic evaluation runner.

Goal:
- Provide different object sets and abstract semantic tasks.
- Ask the LLM to return the final grounded result directly.
- Evaluate:
  1. whether the model understood the task intent (manual field)
  2. whether the return format is correct (auto)
  3. whether the returned content is correct (auto)

Design:
- objects and tasks are decoupled
- the mapping from task -> objects is defined by CASE_BINDINGS
- supports single/batch run
- supports skip/overwrite for existing records
- saves both JSON and CSV
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from openai import OpenAI

import config as cfg


# ============================================================================
# Manual config block
# Edit this section before running the script.
# ============================================================================
RUN_MODE = "single"  # "single" or "batch"
EXISTING_RECORD_POLICY = "skip"  # "skip" or "overwrite"

SELECTED_CASE_IDS = [
    "CASE_001",
]

SELECTED_MODELS = [
    "GPT-4o",
]

SELECTED_TEMPERATURES = [
    0.0,
]

REPEATS = 1
RUN_ID = "E3_object_eval_run_001"

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "e3_object_eval"
OUTPUT_JSON = OUTPUT_DIR / "e3_object_eval.json"
OUTPUT_CSV = OUTPUT_DIR / "e3_object_eval.csv"

SINGLE_TEST_CASE = {
    "case_id": "CASE_001",
    "model": "GPT-4o",
    "temperature": 0.0,
    "repeat_id": 1,
}


FIELDNAMES = [
    "run_id",
    "case_id",
    "task_id",
    "object_set_id",
    "instruction",
    "model_name",
    "temperature",
    "repeat_id",
    "expected_format",
    "expected_result",
    "raw_output",
    "parsed_result",
    "intent_understanding_correct",
    "format_correct",
    "content_correct",
    "human_note",
]


MODEL_REGISTRY = {
    "GPT-4o": {
        "api_key": cfg.GPT_API_KEY,
        "base_url": cfg.GPT_BASE_URL,
        "model_name": cfg.GPT_LLM_MODEL,
    },
    "DeepSeek-V3.2": {
        "api_key": cfg.SILICONFLOW_API_KEY,
        "base_url": cfg.SILICONFLOW_BASE_URL,
        "model_name": cfg.SILICONFLOW_LLM_MODEL,
    },
    "OLLAMA": {
        "api_key": cfg.OLLAMA_API_KEY,
        "base_url": cfg.OLLAMA_BASE_URL,
        "model_name": cfg.OLLAMA_LLM_MODEL,
    },
}


# ============================================================================
# Object sets
# Keep objects reusable and independent from tasks.
# ============================================================================
OBJECT_SETS: Dict[str, Dict[str, List[str]]] = {
    "OBJ_BASIC_FRUITS": {
        "desk": ["desk1", "desk2"],
        "fruits": ["apple", "banana", "pear"],
        "bottle": ["bottle1", "bottle2"],
    },
    "OBJ_BLOCKS": {
        "red_block": ["red_block1", "red_block2"],
        "blue_block": ["blue_block1"],
        "yellow_block": ["yellow_block1"],
        "desk": ["desk1"],
    },
    "OBJ_CHAIRS": {
        "chair": ["chair1", "chair2", "chair3"],
        "bottle": ["bottle1", "bottle2"],
        "fruits": ["lemon"],
    },
}


# ============================================================================
# Task specs
# Keep tasks reusable and independent from object sets.
# expected_format:
#   - "string": expect one object id
#   - "list": expect a list of object ids
# order_matters:
#   - only used when expected_format == "list"
# ============================================================================
TASK_SPECS: Dict[str, Dict[str, Any]] = {
    "TASK_001": {
        "instruction": "object that can be eaten",
        "expected_format": "list",
        "expected_result": ["apple", "banana", "pear"],
        "order_matters": False,
    },
    "TASK_002": {
        "instruction": "the blue bottle",
        "expected_format": "list",
        "expected_result": [],
        "order_matters": False,
    },
    "TASK_003": {
        "instruction": "the leftmost chair",
        "expected_format": "string",
        "expected_result": "chair1",
        "order_matters": True,
    },
}


# ============================================================================
# Case bindings
# You decide which task uses which object set here.
# This is the only place where tasks and objects are tied together.
# ============================================================================
CASE_BINDINGS: List[Dict[str, str]] = [
    {
        "case_id": "CASE_001",
        "task_id": "TASK_001",
        "object_set_id": "OBJ_BASIC_FRUITS",
    },
    {
        "case_id": "CASE_002",
        "task_id": "TASK_002",
        "object_set_id": "OBJ_BASIC_FRUITS",
    },
    {
        "case_id": "CASE_003",
        "task_id": "TASK_003",
        "object_set_id": "OBJ_CHAIRS",
    },
]


SYSTEM_PROMPT = """You are an object grounding assistant.

You will receive:
1. an objects dictionary
2. an abstract semantic task
3. the required output format

Your job is to return the final grounded result directly.

Rules:
- Output JSON only.
- Do not output code.
- Do not explain.
- Use only object ids that appear in the given objects dictionary.
- If the required format is "string", output one object id.
- If the required format is "list", output a JSON list of object ids.

Output schema:
{"result": ...}
"""


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    instruction: str
    expected_format: str
    expected_result: Any
    order_matters: bool


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    task_id: str
    object_set_id: str


class E3ObjectEvaluator:
    def __init__(self) -> None:
        self.output_dir = OUTPUT_DIR
        self.output_json = OUTPUT_JSON
        self.output_csv = OUTPUT_CSV
        self.task_specs = {
            task_id: TaskSpec(task_id=task_id, **task_data)
            for task_id, task_data in TASK_SPECS.items()
        }
        self.case_specs = {
            item["case_id"]: CaseSpec(**item)
            for item in CASE_BINDINGS
        }

    def _load_existing_payload(self) -> dict:
        if not self.output_json.exists():
            return {"meta": {}, "records": []}
        with self.output_json.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        records = payload.get("records", [])
        if not isinstance(records, list):
            raise ValueError(f"Invalid records format in {self.output_json}")
        return {
            "meta": payload.get("meta", {}),
            "records": records,
        }

    def _build_meta(self) -> dict:
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "run_mode": RUN_MODE,
            "existing_record_policy": EXISTING_RECORD_POLICY,
            "run_id": RUN_ID,
            "selected_case_ids": SELECTED_CASE_IDS,
            "selected_models": SELECTED_MODELS,
            "selected_temperatures": SELECTED_TEMPERATURES,
            "repeats": REPEATS,
            "single_test_case": SINGLE_TEST_CASE,
            "fieldnames": FIELDNAMES,
            "output_json": str(self.output_json),
            "output_csv": str(self.output_csv),
        }

    def _write_outputs(self, records: Sequence[dict]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": self._build_meta(),
            "records": list(records),
        }
        with self.output_json.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        with self.output_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(self._serialize_records_for_csv(records))

    def _serialize_records_for_csv(self, records: Sequence[dict]) -> List[dict]:
        csv_records: List[dict] = []
        for record in records:
            item = dict(record)
            for key in ("expected_result", "parsed_result"):
                item[key] = json.dumps(item.get(key), ensure_ascii=False)
            item["raw_output"] = str(item.get("raw_output", ""))
            csv_records.append(item)
        return csv_records

    def _record_key(self, record: dict) -> Tuple[str, str, float, int]:
        return (
            str(record["case_id"]),
            str(record["model_name"]),
            float(record["temperature"]),
            int(record["repeat_id"]),
        )

    def _existing_keys(self, records: Iterable[dict]) -> set[Tuple[str, str, float, int]]:
        return {self._record_key(record) for record in records}

    def _find_record_index(
        self,
        records: Sequence[dict],
        record_key: Tuple[str, str, float, int],
    ) -> Optional[int]:
        for idx, record in enumerate(records):
            if self._record_key(record) == record_key:
                return idx
        return None

    def _validate_config(self) -> None:
        unknown_cases = sorted(set(SELECTED_CASE_IDS) - set(self.case_specs))
        unknown_models = sorted(set(SELECTED_MODELS) - set(MODEL_REGISTRY))
        if unknown_cases:
            raise ValueError(f"Unknown case ids: {unknown_cases}")
        if unknown_models:
            raise ValueError(f"Unknown models: {unknown_models}")
        if not SELECTED_TEMPERATURES:
            raise ValueError("SELECTED_TEMPERATURES cannot be empty")
        if EXISTING_RECORD_POLICY not in {"skip", "overwrite"}:
            raise ValueError(
                f"EXISTING_RECORD_POLICY must be 'skip' or 'overwrite', got: {EXISTING_RECORD_POLICY}"
            )

    def _case_context(self, case_id: str) -> Tuple[CaseSpec, TaskSpec, Dict[str, List[str]]]:
        case = self.case_specs[case_id]
        if case.object_set_id not in OBJECT_SETS:
            raise ValueError(f"Unknown object_set_id in case {case_id}: {case.object_set_id}")
        if case.task_id not in self.task_specs:
            raise ValueError(f"Unknown task_id in case {case_id}: {case.task_id}")
        task = self.task_specs[case.task_id]
        objects = OBJECT_SETS[case.object_set_id]
        return case, task, objects

    def _build_prompt(self, task: TaskSpec, objects: Dict[str, List[str]]) -> str:
        return (
            f"objects = {json.dumps(objects, ensure_ascii=False, indent=2)}\n\n"
            f"task = {json.dumps(task.instruction, ensure_ascii=False)}\n"
            f"required_format = {json.dumps(task.expected_format, ensure_ascii=False)}\n\n"
            "Return JSON only using the schema {\"result\": ...}."
        )

    def _call_llm(self, prompt: str, model_label: str, temperature: float) -> str:
        model_config = MODEL_REGISTRY[model_label]
        client = OpenAI(
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )
        response = client.chat.completions.create(
            model=model_config["model_name"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            top_p=None,
        )
        return response.choices[0].message.content or ""

    def _parse_json_result(self, raw_text: str) -> Tuple[Optional[Any], str]:
        if not raw_text.strip():
            return None, "empty_output"
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                return None, "json_parse_error"
            try:
                payload = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None, "json_parse_error"

        if not isinstance(payload, dict):
            return None, "top_level_not_object"
        if "result" not in payload:
            return None, "missing_result_field"
        return payload["result"], ""

    def _is_string_list(self, value: Any) -> bool:
        return isinstance(value, list) and all(isinstance(item, str) for item in value)

    def _check_format(self, expected_format: str, parsed_result: Any) -> bool:
        if expected_format == "string":
            return isinstance(parsed_result, str)
        if expected_format == "list":
            return self._is_string_list(parsed_result)
        raise ValueError(f"Unsupported expected_format: {expected_format}")

    def _normalize_list(self, value: List[str]) -> List[str]:
        return sorted(value)

    def _check_content(self, task: TaskSpec, parsed_result: Any) -> bool:
        if task.expected_format == "string":
            return parsed_result == task.expected_result
        if task.expected_format == "list":
            if not isinstance(parsed_result, list):
                return False
            if task.order_matters:
                return parsed_result == task.expected_result
            return self._normalize_list(parsed_result) == self._normalize_list(task.expected_result)
        return False

    def _build_record(
        self,
        case: CaseSpec,
        task: TaskSpec,
        model_label: str,
        temperature: float,
        repeat_id: int,
        raw_output: str,
        parsed_result: Any,
        format_correct: str,
        content_correct: str,
        human_note: str,
    ) -> dict:
        return {
            "run_id": RUN_ID,
            "case_id": case.case_id,
            "task_id": task.task_id,
            "object_set_id": case.object_set_id,
            "instruction": task.instruction,
            "model_name": model_label,
            "temperature": temperature,
            "repeat_id": repeat_id,
            "expected_format": task.expected_format,
            "expected_result": task.expected_result,
            "raw_output": raw_output,
            "parsed_result": parsed_result,
            "intent_understanding_correct": "",
            "format_correct": format_correct,
            "content_correct": content_correct,
            "human_note": human_note,
        }

    def run_one_case(self, case_id: str, model_label: str, temperature: float, repeat_id: int) -> dict:
        if case_id not in self.case_specs:
            raise ValueError(f"Unknown case_id: {case_id}")
        if model_label not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_label}")

        case, task, objects = self._case_context(case_id)
        prompt = self._build_prompt(task, objects)

        print("=" * 80)
        print("Running object-semantic evaluation case")
        print(f"case_id      : {case.case_id}")
        print(f"task_id      : {task.task_id}")
        print(f"object_set_id: {case.object_set_id}")
        print(f"instruction  : {task.instruction}")
        print(f"model        : {model_label}")
        print(f"temperature  : {temperature}")
        print(f"repeat_id    : {repeat_id}")
        print(f"expected_fmt : {task.expected_format}")
        print(f"expected_res : {task.expected_result}")
        print("-" * 80)
        print("Objects:")
        print(json.dumps(objects, ensure_ascii=False, indent=2))
        print("-" * 80)
        print("Prompt:")
        print(prompt)
        print("-" * 80)

        raw_output = ""
        parsed_result = None
        human_note = ""
        format_correct = "no"
        content_correct = "no"

        try:
            raw_output = self._call_llm(prompt, model_label, temperature)
            parsed_result, parse_note = self._parse_json_result(raw_output)
            if parse_note:
                human_note = parse_note
            else:
                format_ok = self._check_format(task.expected_format, parsed_result)
                content_ok = format_ok and self._check_content(task, parsed_result)
                format_correct = "yes" if format_ok else "no"
                content_correct = "yes" if content_ok else "no"
        except Exception as exc:
            human_note = f"generation_error: {type(exc).__name__}: {exc}"

        print("Raw model output:")
        print(raw_output or "<empty>")
        print("-" * 80)
        print("Parsed result:")
        print(parsed_result if parsed_result is not None else "<none>")
        print("-" * 80)
        print(f"format_correct : {format_correct}")
        print(f"content_correct: {content_correct}")
        if human_note:
            print(f"human_note     : {human_note}")
        print("=" * 80)

        return self._build_record(
            case=case,
            task=task,
            model_label=model_label,
            temperature=temperature,
            repeat_id=repeat_id,
            raw_output=raw_output,
            parsed_result=parsed_result,
            format_correct=format_correct,
            content_correct=content_correct,
            human_note=human_note,
        )

    def run_single_test(self) -> dict:
        record = self.run_one_case(
            case_id=SINGLE_TEST_CASE["case_id"],
            model_label=SINGLE_TEST_CASE["model"],
            temperature=float(SINGLE_TEST_CASE["temperature"]),
            repeat_id=int(SINGLE_TEST_CASE["repeat_id"]),
        )
        self._write_outputs([record])
        print(f"Saved single-test JSON to: {self.output_json}")
        print(f"Saved single-test CSV  to: {self.output_csv}")
        return record

    def run_batch(self) -> List[dict]:
        self._validate_config()
        existing_payload = self._load_existing_payload()
        records = existing_payload["records"]
        completed_keys = self._existing_keys(records)

        total = len(SELECTED_CASE_IDS) * len(SELECTED_MODELS) * len(SELECTED_TEMPERATURES) * REPEATS
        processed = 0
        skipped = 0

        print(f"Loaded existing records: {len(records)}")
        print(f"Planned combinations    : {total}")

        for case_id in SELECTED_CASE_IDS:
            for model_label in SELECTED_MODELS:
                for temperature in SELECTED_TEMPERATURES:
                    for repeat_id in range(1, REPEATS + 1):
                        probe_record = {
                            "case_id": case_id,
                            "model_name": model_label,
                            "temperature": float(temperature),
                            "repeat_id": repeat_id,
                        }
                        record_key = self._record_key(probe_record)
                        if record_key in completed_keys:
                            if EXISTING_RECORD_POLICY == "skip":
                                skipped += 1
                                print(f"[SKIP] {record_key} already exists")
                                continue
                            print(f"[OVERWRITE] {record_key} already exists and will be replaced")

                        print(f"[RUN ] {record_key}")
                        record = self.run_one_case(
                            case_id=case_id,
                            model_label=model_label,
                            temperature=float(temperature),
                            repeat_id=repeat_id,
                        )
                        existing_index = self._find_record_index(records, record_key)
                        if existing_index is None:
                            records.append(record)
                        else:
                            records[existing_index] = record
                        completed_keys.add(record_key)
                        processed += 1
                        self._write_outputs(records)
                        print(f"[SAVE] progress={processed} new / {skipped} skipped / {len(records)} total saved")

        print("=" * 80)
        print("Batch run finished")
        print(f"new records : {processed}")
        print(f"skipped     : {skipped}")
        print(f"total saved : {len(records)}")
        print(f"json output : {self.output_json}")
        print(f"csv output  : {self.output_csv}")
        print("=" * 80)
        return records


def main() -> None:
    evaluator = E3ObjectEvaluator()
    if RUN_MODE == "single":
        evaluator.run_single_test()
        return
    if RUN_MODE == "batch":
        evaluator.run_batch()
        return
    raise ValueError(f"RUN_MODE must be 'single' or 'batch', got: {RUN_MODE}")


if __name__ == "__main__":
    main()
