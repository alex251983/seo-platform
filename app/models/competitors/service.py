# app/modules/competitors/service.py
from typing import List, Dict, Any
from app.models.seo_data.providers.openserp import OpenSERPProvider
from app.models.seo_data.providers.base import BaseSEOProvider
import structlog

logger = structlog.get_logger()


class CompetitorService:
    def __init__(self, serp_provider: BaseSEOProvider = None):
        self.serp = serp_provider or OpenSERPProvider()

    async def compare_competitors(
        self,
        domains: List[str],
        keywords: List[str],
        search_engine: str = "google",
    ) -> Dict[str, Any]:
        """
        Сравнивает позиции списка доменов по ключевым словам.
        Возвращает словарь:
        {
            "results": {
                domain: {
                    keyword: {"position": int | None, "url": str | None}
                }
            },
            "summary": {
                domain: {
                    "avg_position": float,
                    "visibility": float (доля в топ-10),
                    "keywords_in_top10": int
                }
            },
            "overlap": {
                "keywords_present_in_all": [...],
                "unique_per_domain": {domain: [...]}
            }
        }
        """
        results = {domain: {} for domain in domains}
        for kw in keywords:
            serp_data = await self.serp.get_serp_results(kw, engine=search_engine, limit=20)
            organic = serp_data.get("results", [])
            # Собираем позиции для каждого домена
            for domain in domains:
                position = None
                matched_url = None
                for idx, item in enumerate(organic, start=1):
                    if domain in item.get("link", ""):
                        position = idx
                        matched_url = item.get("link")
                        break
                results[domain][kw] = {"position": position, "url": matched_url}

        # Сводка
        summary = {}
        for domain in domains:
            positions = [res["position"] for res in results[domain].values() if res["position"] is not None]
            avg_pos = sum(positions) / len(positions) if positions else 100
            in_top10 = sum(1 for p in positions if p <= 10)
            summary[domain] = {
                "avg_position": avg_pos,
                "visibility": in_top10 / len(keywords) if keywords else 0,
                "keywords_in_top10": in_top10,
            }

        # Пересечения
        overlap = self._calculate_overlap(results, domains, keywords)

        return {
            "results": results,
            "summary": summary,
            "overlap": overlap,
        }

    @staticmethod
    def _calculate_overlap(results, domains, keywords):
        domain_keyword_sets = {}
        for domain in domains:
            kw_set = set()
            for kw in keywords:
                if results[domain][kw]["position"] is not None:
                    kw_set.add(kw)
            domain_keyword_sets[domain] = kw_set

        all_intersection = set.intersection(*domain_keyword_sets.values()) if domains else set()
        unique_per_domain = {}
        for domain in domains:
            other_domains = set(domains) - {domain}
            union_others = set()
            for other in other_domains:
                union_others |= domain_keyword_sets[other]
            unique = domain_keyword_sets[domain] - union_others
            unique_per_domain[domain] = list(unique)

        return {
            "keywords_present_in_all": list(all_intersection),
            "unique_per_domain": unique_per_domain,
        }