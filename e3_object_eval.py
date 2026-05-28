#!/usr/bin/env python3
"""
E3 object parsing static evaluation runner.

This script evaluates the parse_obj_name-style object parsing chain without
executing any robot actions. It keeps the prompt assembly and code-exec flow
close to the current Big_Brain logic, while making model/temperature/repeats
configurable like e3_static_eval.py.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from openai import OpenAI

import config as cfg
from prompt.object_prompt import OBJECT_PROMPT
from utils.utils import extract_code


# ============================================================================
# Manual config block
# Edit this section before running the script.
# ============================================================================
RUN_MODE = "batch"  # "single" or "batch"
# RUN_MODE = "single"
EXISTING_RECORD_POLICY = "skip"  # "skip" or "overwrite"
# EXISTING_RECORD_POLICY = "overwrite"

print(f"RUN_MODE: {RUN_MODE}")
print(f"EXISTING_RECORD_POLICY: {EXISTING_RECORD_POLICY}")

SELECTED_PARSE_TASK_IDS: List[str] = []
# Empty means run all parse tasks.

SELECTED_MODELS = [
    # "GPT-4o",
    "OLLAMA",
]

SELECTED_TEMPERATURES = [
    0.0,
    0.4,
    0.8,
]

REPEATS = 3
RUN_ID = "E3_object_run_001"

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs" / "e3_object"
OUTPUT_JSON = OUTPUT_DIR / "e3_object_eval.json"
OUTPUT_CSV = OUTPUT_DIR / "e3_object_eval.csv"

SINGLE_TEST_CASE = {
    "parse_task_id": "G1_1",
    "model": "OLLAMA",
    "temperature": 0.0,
    "repeat_id": 1,
}


FIELDNAMES = [
    "run_id",
    "parse_task_id",
    "source_task_id",
    "task_type",
    "parse_text",
    "object_set_id",
    "scene_name",
    "model_name",
    "temperature",
    "repeat_id",
    "raw_output",
    "generated_code",
    "parsed_result",
    "expected_result",
    "format_correct",
    "parse_correct",
    "code_executable",
    "execution_error",
    "human_reference_code",
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


@dataclass(frozen=True)
class ObjectSetSpec:
    object_set_id: str
    scene_name: str
    objects: Dict[str, List[str]]
    object_states: Dict[str, Dict[str, Any]]
    robot_pos: Tuple[float, float] = (0.0, 0.0)


@dataclass(frozen=True)
class ParseTaskSpec:
    task_id: str
    source_task_id: str
    task_type: str
    parse_text: str
    object_set_id: str
    human_reference_code: str
    expected_match_mode: str = "unordered_list"


OBJECT_SETS = [
    {
        "object_set_id": "OS_N2",
        "scene_name": "Single trash can scene",
        "objects": {
            "trash_can": ["trash_can_1"],
        },
        "object_states": {
            "trash_can_1": {"xy": (120.0, 80.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
        },
    },
    {
        "object_set_id": "OS_N3",
        "scene_name": "Trash can square-path scene",
        "objects": {
            "trash_can": ["trash_can_1"],
        },
        "object_states": {
            "trash_can_1": {"xy": (60.0, -40.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
        },
    },
    {
        "object_set_id": "OS_N4",
        "scene_name": "Multiple trash cans scene",
        "objects": {
            "trash_can": ["trash_can_far", "trash_can_mid", "trash_can_best"],
        },
        "object_states": {
            "trash_can_far": {"xy": (200.0, 180.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
            "trash_can_mid": {"xy": (-80.0, 35.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
            "trash_can_best": {"xy": (10.0, -12.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
        },
    },
    {
        "object_set_id": "OS_G1",
        "scene_name": "Colored blocks scene",
        "objects": {
            "block": ["red_block_1", "blue_block_1", "yellow_block_1"],
        },
        "object_states": {
            "red_block_1": {"xy": (30.0, 30.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "blue_block_1": {"xy": (60.0, 30.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
            "yellow_block_1": {"xy": (90.0, 30.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "yellow"},
        },
    },
    {
        "object_set_id": "OS_G2",
        "scene_name": "Ground and table blocks scene",
        "objects": {
            "block": ["red_block_ground", "red_block_table", "blue_block_ground"],
        },
        "object_states": {
            "red_block_ground": {"xy": (10.0, 15.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "red_block_table": {"xy": (100.0, 100.0), "z": 85.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "blue_block_ground": {"xy": (40.0, 12.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
        },
    },
    {
        "object_set_id": "OS_G3",
        "scene_name": "Single table scene",
        "objects": {
            "table": ["table_1"],
        },
        "object_states": {
            "table_1": {"xy": (100.0, 50.0), "z": 0.0, "size": (120.0, 80.0, 75.0), "rgb": "brown"},
        },
    },
    {
        "object_set_id": "OS_G4",
        "scene_name": "Blue and yellow block scene",
        "objects": {
            "block": ["blue_block_1", "yellow_block_1", "red_block_1"],
        },
        "object_states": {
            "blue_block_1": {"xy": (20.0, 20.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
            "yellow_block_1": {"xy": (60.0, 20.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "yellow"},
            "red_block_1": {"xy": (40.0, 50.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
        },
    },
    {
        "object_set_id": "OS_C1",
        "scene_name": "Cup on sofa scene",
        "objects": {
            "cup": ["cup_1", "cup_2"],
            "sofa": ["sofa_1"],
            "chair": ["chair_1"],
        },
        "object_states": {
            "cup_1": {"xy": (205.0, 118.0), "z": 55.0, "size": (8.0, 8.0, 12.0), "rgb": "white"},
            "cup_2": {"xy": (30.0, 20.0), "z": 5.0, "size": (8.0, 8.0, 12.0), "rgb": "blue"},
            "sofa_1": {"xy": (200.0, 120.0), "z": 0.0, "size": (120.0, 60.0, 40.0), "rgb": "gray"},
            "chair_1": {"xy": (-50.0, 80.0), "z": 0.0, "size": (40.0, 40.0, 45.0), "rgb": "black"},
        },
    },
    {
        "object_set_id": "OS_C2",
        "scene_name": "Blocks around a table scene",
        "objects": {
            "block": ["red_block_table", "red_block_ground", "blue_block_1", "yellow_block_1"],
            "table": ["table_1"],
        },
        "object_states": {
            "table_1": {"xy": (100.0, 100.0), "z": 0.0, "size": (120.0, 80.0, 75.0), "rgb": "brown"},
            "red_block_table": {"xy": (110.0, 95.0), "z": 85.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "red_block_ground": {"xy": (10.0, 10.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "blue_block_1": {"xy": (20.0, 80.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
            "yellow_block_1": {"xy": (50.0, 80.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "yellow"},
        },
    },
    {
        "object_set_id": "OS_C3",
        "scene_name": "Ground cleanup scene",
        "objects": {
            "block": ["red_block_ground", "blue_block_table"],
            "cup": ["cup_ground", "cup_table"],
            "bottle": ["bottle_ground", "bottle_shelf"],
            "table": ["table_1"],
            "chair": ["chair_1"],
            "sofa": ["sofa_1"],
            "trash_can": ["trash_can_1"],
        },
        "object_states": {
            "red_block_ground": {"xy": (10.0, 5.0), "z": 3.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "blue_block_table": {"xy": (105.0, 95.0), "z": 85.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
            "cup_ground": {"xy": (15.0, -10.0), "z": 4.0, "size": (8.0, 8.0, 12.0), "rgb": "white"},
            "cup_table": {"xy": (90.0, 110.0), "z": 85.0, "size": (8.0, 8.0, 12.0), "rgb": "green"},
            "bottle_ground": {"xy": (-20.0, 0.0), "z": 6.0, "size": (7.0, 7.0, 20.0), "rgb": "blue"},
            "bottle_shelf": {"xy": (-20.0, 50.0), "z": 60.0, "size": (7.0, 7.0, 20.0), "rgb": "clear"},
            "table_1": {"xy": (100.0, 100.0), "z": 0.0, "size": (120.0, 80.0, 75.0), "rgb": "brown"},
            "chair_1": {"xy": (60.0, 40.0), "z": 0.0, "size": (40.0, 40.0, 45.0), "rgb": "black"},
            "sofa_1": {"xy": (150.0, 120.0), "z": 0.0, "size": (120.0, 60.0, 40.0), "rgb": "gray"},
            "trash_can_1": {"xy": (-50.0, -30.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
        },
    },
    {
        "object_set_id": "OS_C4",
        "scene_name": "Patrol around table scene",
        "objects": {
            "table": ["table_1"],
            "block": ["red_block_1", "blue_block_1"],
            "trash_can": ["trash_can_1"],
        },
        "object_states": {
            "table_1": {"xy": (80.0, 60.0), "z": 0.0, "size": (120.0, 80.0, 75.0), "rgb": "brown"},
            "red_block_1": {"xy": (30.0, 90.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "red"},
            "blue_block_1": {"xy": (110.0, 90.0), "z": 5.0, "size": (5.0, 5.0, 5.0), "rgb": "blue"},
            "trash_can_1": {"xy": (-40.0, -20.0), "z": 0.0, "size": (40.0, 40.0, 60.0), "rgb": "gray"},
        },
    },
]


PARSE_TASKS = [
    {
        "task_id": "N2_1",
        "source_task_id": "N2",
        "task_type": "Navigation",
        "parse_text": "trash can",
        "object_set_id": "OS_N2",
        "human_reference_code": "ret_val = objects['trash_can']",
    },
    {
        "task_id": "N3_1",
        "source_task_id": "N3",
        "task_type": "Navigation",
        "parse_text": "trash can",
        "object_set_id": "OS_N3",
        "human_reference_code": "ret_val = objects['trash_can']",
    },
    {
        "task_id": "N4_1",
        "source_task_id": "N4",
        "task_type": "Navigation",
        "parse_text": "the trash can with the smallest sum of absolute coordinates",
        "object_set_id": "OS_N4",
        "human_reference_code": dedent(
            """
            trash_cans = objects['trash_can']
            min_sum = float('inf')
            closest_trash_can = None
            for trash_can in trash_cans:
                x, y = get_obj_xy(trash_can)
                coord_sum = abs(x) + abs(y)
                if coord_sum < min_sum:
                    min_sum = coord_sum
                    closest_trash_can = trash_can
            ret_val = closest_trash_can
            """
        ).strip(),
        "expected_match_mode": "exact",
    },
    {
        "task_id": "G1_1",
        "source_task_id": "G1",
        "task_type": "Manipulation",
        "parse_text": "red block",
        "object_set_id": "OS_G1",
        "human_reference_code": dedent(
            """
            ret_val = []
            for obj_name in objects['block']:
                if get_obj_rgb(obj_name) == 'red':
                    ret_val.append(obj_name)
            """
        ).strip(),
    },
    {
        "task_id": "G2_1",
        "source_task_id": "G2",
        "task_type": "Manipulation",
        "parse_text": "red block on the ground",
        "object_set_id": "OS_G2",
        "human_reference_code": dedent(
            """
            ret_val = []
            for obj_name in objects['block']:
                if get_obj_rgb(obj_name) == 'red':
                    z = get_obj_z(obj_name)
                    if 0 < z < 10:
                        ret_val.append(obj_name)
            """
        ).strip(),
    },
    {
        "task_id": "G3_1",
        "source_task_id": "G3",
        "task_type": "Manipulation",
        "parse_text": "table",
        "object_set_id": "OS_G3",
        "human_reference_code": "ret_val = objects['table']",
    },
    {
        "task_id": "G4_1",
        "source_task_id": "G4",
        "task_type": "Manipulation",
        "parse_text": "blue block",
        "object_set_id": "OS_G4",
        "human_reference_code": dedent(
            """
            ret_val = []
            for obj_name in objects['block']:
                if get_obj_rgb(obj_name) == 'blue':
                    ret_val.append(obj_name)
            """
        ).strip(),
    },
    {
        "task_id": "G4_2",
        "source_task_id": "G4",
        "task_type": "Manipulation",
        "parse_text": "yellow block",
        "object_set_id": "OS_G4",
        "human_reference_code": dedent(
            """
            ret_val = []
            for obj_name in objects['block']:
                if get_obj_rgb(obj_name) == 'yellow':
                    ret_val.append(obj_name)
            """
        ).strip(),
    },
    {
        "task_id": "C1_1",
        "source_task_id": "C1",
        "task_type": "Composite",
        "parse_text": "cup on the sofa",
        "object_set_id": "OS_C1",
        "human_reference_code": dedent(
            """
            ret_val = []
            for cup_name in objects['cup']:
                cup_x, cup_y = get_obj_xy(cup_name)
                cup_z = get_obj_z(cup_name)
                for sofa_name in objects['sofa']:
                    sofa_x, sofa_y = get_obj_xy(sofa_name)
                    sofa_size_x, sofa_size_y, sofa_size_z = get_obj_size(sofa_name)
                    if sofa_x - sofa_size_x / 2 < cup_x < sofa_x + sofa_size_x / 2 and sofa_y - sofa_size_y / 2 < cup_y < sofa_y + sofa_size_y / 2 and cup_z > sofa_size_z:
                        ret_val.append(cup_name)
            """
        ).strip(),
    },
    {
        "task_id": "C1_2",
        "source_task_id": "C1",
        "task_type": "Composite",
        "parse_text": "chair",
        "object_set_id": "OS_C1",
        "human_reference_code": "ret_val = objects['chair']",
    },
    {
        "task_id": "C2_1",
        "source_task_id": "C2",
        "task_type": "Composite",
        "parse_text": "red block on the table",
        "object_set_id": "OS_C2",
        "human_reference_code": dedent(
            """
            ret_val = []
            for block_name in objects['block']:
                for table_name in objects['table']:
                    table_x, table_y = get_obj_xy(table_name)
                    table_size_x, table_size_y, table_size_z = get_obj_size(table_name)
                    block_x, block_y = get_obj_xy(block_name)
                    block_z = get_obj_z(block_name)
                    if table_x - table_size_x / 2 < block_x < table_x + table_size_x / 2 and table_y - table_size_y / 2 < block_y < table_y + table_size_y / 2 and block_z > table_size_z:
                        if get_obj_rgb(block_name) == 'red':
                            ret_val.append(block_name)
            """
        ).strip(),
    },
    {
        "task_id": "C2_2",
        "source_task_id": "C2",
        "task_type": "Composite",
        "parse_text": "blue block",
        "object_set_id": "OS_C2",
        "human_reference_code": dedent(
            """
            ret_val = []
            for block_name in objects['block']:
                if get_obj_rgb(block_name) == 'blue':
                    ret_val.append(block_name)
            """
        ).strip(),
    },
    {
        "task_id": "C2_3",
        "source_task_id": "C2",
        "task_type": "Composite",
        "parse_text": "yellow block",
        "object_set_id": "OS_C2",
        "human_reference_code": dedent(
            """
            ret_val = []
            for block_name in objects['block']:
                if get_obj_rgb(block_name) == 'yellow':
                    ret_val.append(block_name)
            """
        ).strip(),
    },
    {
        "task_id": "C3_1",
        "source_task_id": "C3",
        "task_type": "Composite",
        "parse_text": "objects on the ground that are not furniture",
        "object_set_id": "OS_C3",
        "human_reference_code": dedent(
            """
            ret_val = []
            for obj_name in objects['block'] + objects['cup'] + objects['bottle']:
                obj_x, obj_y = get_obj_xy(obj_name)
                obj_z = get_obj_z(obj_name)
                if obj_z < 10:
                    ret_val.append(obj_name)
            """
        ).strip(),
    },
    {
        "task_id": "C3_2",
        "source_task_id": "C3",
        "task_type": "Composite",
        "parse_text": "trash can",
        "object_set_id": "OS_C3",
        "human_reference_code": "ret_val = objects['trash_can']",
    },
    {
        "task_id": "C4_1",
        "source_task_id": "C4",
        "task_type": "Composite",
        "parse_text": "table",
        "object_set_id": "OS_C4",
        "human_reference_code": "ret_val = objects['table']",
    },
    {
        "task_id": "C4_2",
        "source_task_id": "C4",
        "task_type": "Composite",
        "parse_text": "red block",
        "object_set_id": "OS_C4",
        "human_reference_code": dedent(
            """
            ret_val = []
            for block_name in objects['block']:
                block_x, block_y = get_obj_xy(block_name)
                if get_obj_rgb(block_name) == 'red':
                    ret_val.append(block_name)
            """
        ).strip(),
    },
    {
        "task_id": "C4_3",
        "source_task_id": "C4",
        "task_type": "Composite",
        "parse_text": "trash can",
        "object_set_id": "OS_C4",
        "human_reference_code": "ret_val = objects['trash_can']",
    },
]


class E3ObjectEvaluator:
    def __init__(self) -> None:
        self.output_dir = OUTPUT_DIR
        self.output_json = OUTPUT_JSON
        self.output_csv = OUTPUT_CSV
        self.object_sets = {
            item["object_set_id"]: ObjectSetSpec(**item) for item in OBJECT_SETS
        }
        self.tasks = {
            item["task_id"]: ParseTaskSpec(**item) for item in PARSE_TASKS
        }
        self.expected_results = self._build_expected_results()

    def _build_expected_results(self) -> Dict[str, Any]:
        expected_results: Dict[str, Any] = {}
        for task in self.tasks.values():
            scene = self.object_sets[task.object_set_id]
            exec_result = self._execute_code(task.human_reference_code, scene)
            if not exec_result["code_executable"] or not exec_result["format_correct"]:
                raise ValueError(
                    f"Invalid human reference code for task {task.task_id}: "
                    f"{exec_result['execution_error']}"
                )
            expected_results[task.task_id] = exec_result["parsed_result"]
        return expected_results

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
            writer.writerows(records)

    def _build_meta(self) -> dict:
        selected_task_ids = SELECTED_PARSE_TASK_IDS or sorted(self.tasks)
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "run_mode": RUN_MODE,
            "existing_record_policy": EXISTING_RECORD_POLICY,
            "run_id": RUN_ID,
            "selected_parse_task_ids": selected_task_ids,
            "selected_models": SELECTED_MODELS,
            "selected_temperatures": SELECTED_TEMPERATURES,
            "repeats": REPEATS,
            "single_test_case": SINGLE_TEST_CASE,
            "fieldnames": FIELDNAMES,
            "output_json": str(self.output_json),
            "output_csv": str(self.output_csv),
        }

    def _record_key(self, record: dict) -> Tuple[str, str, float, int]:
        return (
            str(record["parse_task_id"]),
            str(record["model_name"]),
            float(record["temperature"]),
            int(record["repeat_id"]),
        )

    def _existing_keys(self, records: Iterable[dict]) -> set[Tuple[str, str, float, int]]:
        return {self._record_key(record) for record in records}

    def _validate_selection(
        self,
        task_ids: Sequence[str],
        models: Sequence[str],
        temperatures: Sequence[float],
    ) -> None:
        effective_task_ids = task_ids or sorted(self.tasks)
        unknown_tasks = sorted(set(effective_task_ids) - set(self.tasks))
        unknown_models = sorted(set(models) - set(MODEL_REGISTRY))
        if unknown_tasks:
            raise ValueError(f"Unknown parse task ids: {unknown_tasks}")
        if unknown_models:
            raise ValueError(f"Unknown models: {unknown_models}")
        if not temperatures:
            raise ValueError("SELECTED_TEMPERATURES cannot be empty")
        if EXISTING_RECORD_POLICY not in {"skip", "overwrite"}:
            raise ValueError(
                f"EXISTING_RECORD_POLICY must be 'skip' or 'overwrite', got: {EXISTING_RECORD_POLICY}"
            )

    def _find_record_index(
        self,
        records: Sequence[dict],
        record_key: Tuple[str, str, float, int],
    ) -> Optional[int]:
        for idx, record in enumerate(records):
            if self._record_key(record) == record_key:
                return idx
        return None

    def _build_prompt(self, parse_text: str, objects: Dict[str, List[str]]) -> str:
        objects_str = "objects = {\n"
        for category, obj_list in objects.items():
            objects_str += f'    "{category}": {obj_list},\n'
        objects_str += "}\n"
        return OBJECT_PROMPT + "\n" + objects_str + f"# {parse_text}\n?"

    def _call_object_llm(self, prompt: str, model_label: str, temperature: float) -> str:
        model_config = MODEL_REGISTRY[model_label]
        client = OpenAI(
            api_key=model_config["api_key"],
            base_url=model_config["base_url"],
        )
        response = client.chat.completions.create(
            model=model_config["model_name"],
            messages=[
                {"role": "system", "content": "you only need to use code to answer the ? part"},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            top_p=None,
        )
        return response.choices[0].message.content or ""

    def _unwrap_object_name(self, obj: Any) -> str:
        if isinstance(obj, list):
            if len(obj) != 1:
                raise ValueError(f"Expected a single object, got list: {obj}")
            return self._unwrap_object_name(obj[0])
        if isinstance(obj, tuple):
            if len(obj) != 1:
                raise ValueError(f"Expected a single object, got tuple: {obj}")
            return self._unwrap_object_name(obj[0])
        if not isinstance(obj, str):
            raise TypeError(f"Object name must be str, got: {type(obj).__name__}")
        return obj

    def _build_exec_env(self, scene: ObjectSetSpec) -> Dict[str, Any]:
        object_states = scene.object_states

        def get_obj_xy(object_name: Any) -> Tuple[float, float]:
            resolved_name = self._unwrap_object_name(object_name)
            xy = object_states[resolved_name]["xy"]
            return float(xy[0]), float(xy[1])

        def get_obj_z(object_name: Any) -> float:
            resolved_name = self._unwrap_object_name(object_name)
            return float(object_states[resolved_name]["z"])

        def get_obj_size(object_name: Any) -> Tuple[float, float, float]:
            resolved_name = self._unwrap_object_name(object_name)
            size = object_states[resolved_name]["size"]
            return float(size[0]), float(size[1]), float(size[2])

        def get_obj_rgb(object_name: Any) -> str:
            resolved_name = self._unwrap_object_name(object_name)
            return str(object_states[resolved_name]["rgb"])

        def get_robot_pos() -> Tuple[float, float]:
            return float(scene.robot_pos[0]), float(scene.robot_pos[1])

        return {
            "__builtins__": __builtins__,
            "np": np,
            "objects": scene.objects,
            "get_obj_xy": get_obj_xy,
            "get_obj_z": get_obj_z,
            "get_obj_size": get_obj_size,
            "get_obj_rgb": get_obj_rgb,
            "get_robot_pos": get_robot_pos,
        }

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, np.ndarray):
            return self._normalize_value(value.tolist())
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, tuple):
            return [self._normalize_value(item) for item in value]
        if isinstance(value, list):
            return [self._normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._normalize_value(val) for key, val in value.items()}
        return value

    def _canonicalize_unordered_list(self, value: Any) -> List[str]:
        normalized = self._normalize_value(value)
        if isinstance(normalized, list):
            return sorted(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in normalized)
        return [json.dumps(normalized, ensure_ascii=False, sort_keys=True)]

    def _compare_results(self, actual: Any, expected: Any, match_mode: str) -> bool:
        if match_mode == "exact":
            return self._normalize_value(actual) == self._normalize_value(expected)
        if match_mode == "unordered_list":
            return self._canonicalize_unordered_list(actual) == self._canonicalize_unordered_list(expected)
        raise ValueError(f"Unknown expected_match_mode: {match_mode}")

    def _execute_code(self, code: str, scene: ObjectSetSpec) -> dict:
        exec_env = self._build_exec_env(scene)
        execution_error = ""
        code_executable = True
        try:
            exec(code, exec_env, exec_env)
        except Exception as exc:
            code_executable = False
            execution_error = f"{type(exc).__name__}: {exc}"

        format_correct = "ret_val" in exec_env
        parsed_result = self._normalize_value(exec_env.get("ret_val")) if format_correct else None
        return {
            "format_correct": format_correct,
            "code_executable": code_executable,
            "parsed_result": parsed_result,
            "execution_error": execution_error,
        }

    def _serialize_result(self, value: Any) -> str:
        if value is None:
            return ""
        return json.dumps(self._normalize_value(value), ensure_ascii=False)

    def _build_record(
        self,
        task: ParseTaskSpec,
        scene: ObjectSetSpec,
        model_label: str,
        temperature: float,
        repeat_id: int,
        raw_output: str,
        generated_code: str,
        exec_result: dict,
        human_note: str = "",
    ) -> dict:
        expected_result = self.expected_results[task.task_id]
        parse_correct = (
            exec_result["code_executable"]
            and exec_result["format_correct"]
            and self._compare_results(
                actual=exec_result["parsed_result"],
                expected=expected_result,
                match_mode=task.expected_match_mode,
            )
        )
        return {
            "run_id": RUN_ID,
            "parse_task_id": task.task_id,
            "source_task_id": task.source_task_id,
            "task_type": task.task_type,
            "parse_text": task.parse_text,
            "object_set_id": scene.object_set_id,
            "scene_name": scene.scene_name,
            "model_name": model_label,
            "temperature": temperature,
            "repeat_id": repeat_id,
            "raw_output": raw_output,
            "generated_code": generated_code,
            "parsed_result": self._serialize_result(exec_result["parsed_result"]),
            "expected_result": self._serialize_result(expected_result),
            "format_correct": "yes" if exec_result["format_correct"] else "no",
            "parse_correct": "yes" if parse_correct else "no",
            "code_executable": "yes" if exec_result["code_executable"] else "no",
            "execution_error": exec_result["execution_error"],
            "human_reference_code": task.human_reference_code,
            "human_note": human_note,
        }

    def run_one_case(
        self,
        parse_task_id: str,
        model_label: str,
        temperature: float,
        repeat_id: int,
    ) -> dict:
        self._validate_selection([parse_task_id], [model_label], [temperature])
        task = self.tasks[parse_task_id]
        scene = self.object_sets[task.object_set_id]
        prompt = self._build_prompt(task.parse_text, scene.objects)

        print("=" * 80)
        print("Running single object parsing evaluation case")
        print(f"parse_task_id : {task.task_id}")
        print(f"source_task   : {task.source_task_id}")
        print(f"task_type     : {task.task_type}")
        print(f"parse_text    : {task.parse_text}")
        print(f"object_set_id : {scene.object_set_id}")
        print(f"scene_name    : {scene.scene_name}")
        print(f"model         : {model_label}")
        print(f"temperature   : {temperature}")
        print(f"repeat_id     : {repeat_id}")
        print("-" * 80)
        print("Prompt tail:")
        print("\n".join(prompt.splitlines()[-12:]))
        print("-" * 80)

        raw_output = ""
        generated_code = ""
        human_note = ""
        exec_result = {
            "format_correct": False,
            "code_executable": False,
            "parsed_result": None,
            "execution_error": "",
        }

        try:
            raw_output = self._call_object_llm(prompt, model_label, temperature)
            generated_code = extract_code(raw_output, task.parse_text)
            exec_result = self._execute_code(generated_code, scene)
        except Exception as exc:
            human_note = f"generation_error: {type(exc).__name__}: {exc}"
            exec_result["execution_error"] = human_note

        print("Raw model output:")
        print(raw_output or "<empty>")
        print("-" * 80)
        print("\033[1;31mExtracted generated_code:\033[0m")
        print(generated_code or "<empty>")
        print("-" * 80)
        print(f"expected_result : {self._serialize_result(self.expected_results[task.task_id])}")
        print(f"parsed_result   : {self._serialize_result(exec_result['parsed_result']) or '<empty>'}")
        print(f"format_correct  : {exec_result['format_correct']}")
        print(f"code_executable : {exec_result['code_executable']}")
        print(f"execution_error : {exec_result['execution_error'] or '<empty>'}")
        if human_note:
            print("-" * 80)
            print(f"Note: {human_note}")
        print("=" * 80)

        return self._build_record(
            task=task,
            scene=scene,
            model_label=model_label,
            temperature=temperature,
            repeat_id=repeat_id,
            raw_output=raw_output,
            generated_code=generated_code,
            exec_result=exec_result,
            human_note=human_note,
        )

    def run_single_test(self) -> dict:
        record = self.run_one_case(
            parse_task_id=SINGLE_TEST_CASE["parse_task_id"],
            model_label=SINGLE_TEST_CASE["model"],
            temperature=float(SINGLE_TEST_CASE["temperature"]),
            repeat_id=int(SINGLE_TEST_CASE["repeat_id"]),
        )
        self._write_outputs([record])
        print(f"Saved single-test JSON to: {self.output_json}")
        print(f"Saved single-test CSV  to: {self.output_csv}")
        return record

    def run_batch(self) -> List[dict]:
        selected_task_ids = SELECTED_PARSE_TASK_IDS or sorted(self.tasks)
        self._validate_selection(selected_task_ids, SELECTED_MODELS, SELECTED_TEMPERATURES)

        existing_payload = self._load_existing_payload()
        records = existing_payload["records"]
        completed_keys = self._existing_keys(records)

        total = len(selected_task_ids) * len(SELECTED_MODELS) * len(SELECTED_TEMPERATURES) * REPEATS
        processed = 0
        skipped = 0

        print(f"Loaded existing records: {len(records)}")
        print(f"Planned combinations    : {total}")

        for parse_task_id in selected_task_ids:
            task = self.tasks[parse_task_id]
            scene = self.object_sets[task.object_set_id]
            for model_label in SELECTED_MODELS:
                for temperature in SELECTED_TEMPERATURES:
                    for repeat_id in range(1, REPEATS + 1):
                        probe_record = {
                            "parse_task_id": task.task_id,
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

                        print(f"[RUN ] {record_key} scene={scene.object_set_id}")
                        record = self.run_one_case(
                            parse_task_id=parse_task_id,
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
