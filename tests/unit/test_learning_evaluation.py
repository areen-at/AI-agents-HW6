from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ai_agents_hw6.application.learning_eval import evaluate_learning
from ai_agents_hw6.config import load_config


class LearningEvaluationTests(unittest.TestCase):
    def test_evaluation_compares_six_game_baseline_without_training_seed_leak(self) -> None:
        config_data = json.loads(Path("config.json").read_text(encoding="utf-8"))
        config_data["learning"]["evaluation_seed"] = 3030
        config_data["learning"]["training_seed"] = 2020
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data["learning"]["cop_table_path"] = str(Path(temp_dir) / "cop.json")
            config_data["learning"]["thief_table_path"] = str(Path(temp_dir) / "thief.json")
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(json.dumps(config_data), encoding="utf-8")
            result = evaluate_learning(load_config(config_path))

        self.assertEqual(result["evaluation_seed"], 3030)
        self.assertEqual(result["baseline"]["valid_games"], 6)
        self.assertEqual(result["learning"]["valid_games"], 6)
        self.assertEqual(result["baseline"]["illegal_actions"], 0)
        self.assertEqual(result["learning"]["illegal_actions"], 0)
        self.assertIn(result["recommended_runtime_policy"], {"heuristic", "q-learning"})


if __name__ == "__main__":
    unittest.main()
