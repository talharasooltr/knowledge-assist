import unittest
from types import SimpleNamespace

from app.infrastructure.retrieval.pdf_vector_store import _reciprocal_rank_fusion


class HybridRetrievalTests(unittest.TestCase):
    def test_reciprocal_rank_fusion_rewards_chunks_found_by_both_searches(self):
        vector_results = [
            SimpleNamespace(id="vector-first"),
            SimpleNamespace(id="shared"),
            SimpleNamespace(id="vector-third"),
        ]
        lexical_results = [
            SimpleNamespace(id="shared"),
            SimpleNamespace(id="lexical-second"),
        ]

        results = _reciprocal_rank_fusion(
            [vector_results, lexical_results],
            limit=3,
        )

        self.assertEqual([result.id for result in results], [
            "shared",
            "vector-first",
            "lexical-second",
        ])

    def test_reciprocal_rank_fusion_respects_requested_limit(self):
        results = _reciprocal_rank_fusion(
            [[SimpleNamespace(id=str(index)) for index in range(5)]],
            limit=2,
        )

        self.assertEqual(len(results), 2)


if __name__ == "__main__":
    unittest.main()
