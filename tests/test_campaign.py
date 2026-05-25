import sys
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from elbench.config import load_project_config  # noqa: E402
from elbench.execution.campaign import (  # noqa: E402
    build_default_api_pools,
    inspect_model_state,
    is_quota_exhausted_error,
)


class CampaignPlanningTest(unittest.TestCase):
    def test_default_pools_keep_target_apis_separate_and_exclude_expensive_or_incompatible_models(self) -> None:
        config = load_project_config(ROOT / "configs")

        pools = {pool.pool_id: pool for pool in build_default_api_pools(config)}

        self.assertIn("innospark_relay", pools)
        self.assertIn("external_support", pools)

        innospark_models = pools["innospark_relay"].model_ids
        external_models = pools["external_support"].model_ids

        self.assertIn("doubao-seed-2-0-pro-260215", innospark_models)
        self.assertIn("deepseek-r1-250528", innospark_models)
        self.assertIn("kimi-k2.6", innospark_models)
        self.assertIn("deepseek-v3.2", innospark_models)
        self.assertIn("gemini-3.1-pro-preview", innospark_models)
        self.assertNotIn("gemini-3-flash-preview", innospark_models)

        self.assertIn("gpt-5.4", external_models)
        self.assertIn("claude-sonnet-4-6", external_models)
        self.assertIn("claude-opus-4-6", external_models)
        self.assertNotIn("gpt-5.2-pro", external_models)
        self.assertFalse(set(innospark_models) & set(external_models))

    def test_quota_detection_recognizes_common_relay_messages(self) -> None:
        self.assertTrue(is_quota_exhausted_error(RuntimeError("insufficient quota")))
        self.assertTrue(is_quota_exhausted_error(RuntimeError("账号额度不足")))
        self.assertFalse(is_quota_exhausted_error(RuntimeError("ReadTimeout")))

    def test_state_inspection_uses_requested_campaign_prefix_only(self) -> None:
        config = load_project_config(ROOT / "configs")
        original_output_root = config.app.output_root
        temp_root = ROOT / "tmp_test_artifacts" / "campaign_state"
        try:
            config.app.output_root = temp_root
            safe_model_id = "doubao-seed-2-0-pro-260215"
            old_summary = temp_root / "summaries" / "old-run" / f"{safe_model_id}.summary.json"
            old_summary.parent.mkdir(parents=True, exist_ok=True)
            old_summary.write_text(
                '{"total_judged": 9999, "total_failures": 0}',
                encoding="utf-8",
            )

            state = inspect_model_state(
                config=config,
                model_id=safe_model_id,
                modules={"通用模型"},
                run_prefix="campaign-official",
            )

            self.assertEqual(state.run_id, "campaign-official-doubao-seed-2-0-pro-260215")
            self.assertTrue(state.needs_run)
        finally:
            config.app.output_root = original_output_root
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
