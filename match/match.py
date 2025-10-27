import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
class AdvancedMatcher:

    def __init__(self, storage):
        self.storage = storage
        
        # 字段权重
        self.field_weights = {
            "skills_experience": 0.5,
            "education_certifications": 0.3,
            "projects_achievements": 0.2
        }
        
        # 评分策略
        self.scoring_strategies = {
            "average": self._average_score,
            "max": self._max_score,
            "weighted_average": self._weighted_average_score
        }
    
    def match_resumes_to_jd(
        self,
        jd_id: str,
        top_k: int = 10,
        min_score: float = 0.0,
        required_fields: Optional[List[str]] = None,
        strategy: str = "weighted_average"
    ) -> List[Dict]:
        """
        高级匹配
        
        Args:
            jd_id: JD ID
            top_k: 返回数量
            min_score: 最低分数阈值
            required_fields: 必须匹配的字段
            strategy: 评分策略 ('average', 'max', 'weighted_average')
        """
        
        # 获取 JD chunks
        jd_chunks = self.storage.get_chunks_by_document(jd_id)
        
        if not jd_chunks:
            return []
        
        print(f"📋 JD 包含 {len(jd_chunks)} 个 chunks")
        
        # 收集所有匹配
        resume_matches = defaultdict(lambda: {
            "field_scores": defaultdict(list),
            "all_chunks": []
        })
        
        # 对每个 JD chunk 进行搜索
        for jd_chunk in jd_chunks:
            field = jd_chunk['metadata']['field']
            
            similar_chunks = self.storage.search_similar_chunks(
                query_text=jd_chunk['content'],
                document_type="resume",
                field=field,
                top_k=20
            )
            
            for match in similar_chunks:
                resume_id = match['metadata']['document_id']
                resume_matches[resume_id]["field_scores"][field].append(
                    match['similarity']
                )
                resume_matches[resume_id]["all_chunks"].append({
                    "jd_field": field,
                    "resume_chunk": match['chunk_id'],
                    "similarity": match['similarity'],
                    "content": match['content'][:100]
                })
        
        # 计算最终分数
        scoring_func = self.scoring_strategies.get(
            strategy, 
            self._weighted_average_score
        )
        
        final_scores = []
        
        for resume_id, data in resume_matches.items():
            # 检查必需字段
            if required_fields:
                has_all_required = all(
                    field in data["field_scores"] 
                    for field in required_fields
                )
                if not has_all_required:
                    continue
            
            # 计算分数
            score, field_details = scoring_func(data["field_scores"])
            
            # 过滤低分
            if score < min_score:
                continue
            
            final_scores.append({
                "resume_id": resume_id,
                "score": score,
                "field_scores": field_details,
                "matched_fields": list(data["field_scores"].keys()),
                "total_matches": len(data["all_chunks"]),
                "top_matches": sorted(
                    data["all_chunks"], 
                    key=lambda x: x['similarity'], 
                    reverse=True
                )[:3]  # 前3个最匹配的 chunks
            })
        
        # 排序
        final_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return final_scores[:top_k]
    
    def _average_score(self, field_scores: Dict) -> Tuple[float, Dict]:
        """平均分策略"""
        all_scores = []
        field_details = {}
        
        for field, scores in field_scores.items():
            avg = sum(scores) / len(scores)
            all_scores.append(avg)
            field_details[field] = {"score": avg, "count": len(scores)}
        
        final_score = sum(all_scores) / len(all_scores) if all_scores else 0
        return final_score, field_details
    
    def _max_score(self, field_scores: Dict) -> Tuple[float, Dict]:
        """最大分策略（取最好的匹配）"""
        field_details = {}
        max_scores = []
        
        for field, scores in field_scores.items():
            max_score = max(scores)
            max_scores.append(max_score)
            field_details[field] = {"score": max_score, "count": len(scores)}
        
        final_score = max(max_scores) if max_scores else 0
        return final_score, field_details
    
    def _weighted_average_score(self, field_scores: Dict) -> Tuple[float, Dict]:
        """加权平均策略"""
        weighted_score = 0.0
        total_weight = 0.0
        field_details = {}
        
        for field, scores in field_scores.items():
            avg_score = sum(scores) / len(scores)
            weight = self.field_weights.get(field, 0.1)
            
            weighted_score += avg_score * weight
            total_weight += weight
            
            field_details[field] = {
                "score": avg_score,
                "weight": weight,
                "weighted_score": avg_score * weight,
                "count": len(scores)
            }
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        return final_score, field_details
    
    def get_match_explanation(
        self, 
        jd_id: str, 
        resume_id: str
    ) -> Dict:
        """
        详细解释为什么这份简历匹配这个 JD
        """
        jd_chunks = self.storage.get_chunks_by_document(jd_id)
        resume_chunks = self.storage.get_chunks_by_document(resume_id)
        
        explanations = []
        
        for jd_chunk in jd_chunks:
            # 找到最匹配的 resume chunk
            similar = self.storage.search_similar_chunks(
                query_text=jd_chunk['content'],
                document_type="resume",
                top_k=1
            )
            
            if similar and similar[0]['metadata']['document_id'] == resume_id:
                explanations.append({
                    "jd_requirement": jd_chunk['content'][:200],
                    "resume_match": similar[0]['content'][:200],
                    "similarity": similar[0]['similarity'],
                    "field": jd_chunk['metadata']['field']
                })
        
        return {
            "jd_id": jd_id,
            "resume_id": resume_id,
            "matches": explanations,
            "overall_match_count": len(explanations)
        }


# ===== 完整使用示例 =====
if __name__ == "__main__":
    from chroma_storage import ChromaDBStorage
    
    # 初始化
    storage = ChromaDBStorage()
    matcher = AdvancedMatcher(storage)
    
    # 匹配
    print("🚀 开始匹配...")
    results = matcher.match_resumes_to_jd(
        jd_id="jd_001",
        top_k=10,
        min_score=0.5,  # 只返回分数 > 0.5 的
        required_fields=["skills_experience"],  # 必须有技能经验匹配
        strategy="weighted_average"
    )
    
    # 打印结果
    print("\n" + "="*70)
    print("🎯 匹配结果")
    print("="*70)
    
    for i, result in enumerate(results, 1):
        print(f"\n{'='*70}")
        print(f"排名 #{i}: {result['resume_id']}")
        print(f"总分: {result['score']:.2%}")
        print(f"匹配字段: {', '.join(result['matched_fields'])}")
        print(f"总匹配数: {result['total_matches']}")
        
        print("\n各字段详情:")
        for field, details in result['field_scores'].items():
            print(f"  {field}:")
            print(f"    分数: {details['score']:.2%}")
            if 'weight' in details:
                print(f"    权重: {details['weight']}")
                print(f"    加权分: {details['weighted_score']:.2%}")
        
        print("\n前3个最佳匹配:")
        for j, match in enumerate(result['top_matches'], 1):
            print(f"  {j}. [{match['jd_field']}] 相似度 {match['similarity']:.2%}")
            print(f"     {match['content']}...")
    
    # 详细解释某个匹配
    if results:
        print("\n" + "="*70)
        print("📖 详细匹配解释")
        print("="*70)
        
        explanation = matcher.get_match_explanation(
            jd_id="jd_001",
            resume_id=results[0]['resume_id']
        )
        
        print(f"\nJD: {explanation['jd_id']}")
        print(f"Resume: {explanation['resume_id']}")
        print(f"匹配点数: {explanation['overall_match_count']}\n")
        
        for i, match in enumerate(explanation['matches'], 1):
            print(f"{i}. [{match['field']}] 相似度: {match['similarity']:.2%}")
            print(f"   JD要求: {match['jd_requirement']}...")
            print(f"   简历匹配: {match['resume_match']}...")
            print()

