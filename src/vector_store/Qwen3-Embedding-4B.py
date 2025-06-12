import openai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 初始化 OpenAI 客户端
client = openai.OpenAI(
    base_url="https://mgallery.haier.net/v1",
    api_key="sk-9RT5LGHtQWALI9bm92B40186Da7148068738C4Dd218499E2"  # 如果没有启用鉴权，设为 EMPTY 即可
)

def get_embedding(text):
    """
    获取文本的 embedding 向量    
    """
    response = client.embeddings.create(
        model="Qwen3-Embedding-4B",  # 对应 --served-model-name
        input=text
    )
    
    return response.data[0].embedding

def test_single_embedding():
    print("=== 测试1：获取单个文本 Embedding ===")
    text = "人工智能是未来科技发展的核心方向。"
    emb = get_embedding(text)
    print(f"文本：{text}")
    print(f"Embedding 维度：{len(emb)}")
    print(f"前5个维度值：{emb[:5]}")

def test_similarity():
    print("\n=== 测试2：计算语义相似度 ===")
    text1 = "如何申请护照？"
    text2 = "办理护照需要准备身份证、户口本、照片等材料。"
    text3 = "护照的有效期是10年。"

    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    emb3 = get_embedding(text3)

    sim1 = cosine_similarity([emb1], [emb2])[0][0]
    sim2 = cosine_similarity([emb1], [emb3])[0][0]

    print(f"文本1：{text1}")
    print(f"文本2：{text2} -> 相似度：{sim1:.4f}")
    print(f"文本3：{text3} -> 相似度：{sim2:.4f}")

def test_zero_shot_classification():
    print("\n=== 测试3：Zero-shot 文本分类 ===")
    text = "这部电影节奏紧凑，特效震撼，剧情有深度。"
    candidates = ["正面评价", "负面评价", "中立评价"]

    text_emb = get_embedding(text)
    candidate_embs = [get_embedding(label) for label in candidates]

    scores = [
        cosine_similarity([text_emb], [emb])[0][0]
        for emb in candidate_embs
    ]

    best_label = candidates[np.argmax(scores)]

    print(f"输入文本：{text}")
    for label, score in zip(candidates, scores):
        print(f"类别：{label} -> 匹配得分：{score:.4f}")
    print(f"预测分类：{best_label}")

def test_batch_embeddings():
    print("\n=== 测试4：批量获取 Embedding ===")
    texts = [
        "北京是中国的首都。",
        "上海是一座国际化大都市。",
        "成都以美食和大熊猫闻名于世。"
    ]
    response = client.embeddings.create(
        model="Qwen3-Embedding-4B",
        input=texts
    )
    embeddings = [data.embedding for data in response.data]
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        print(f"文本{i+1}: {text}")
        print(f"前5个维度：{emb[:5]}")

if __name__ == "__main__":
    test_single_embedding()
    test_similarity()
    test_zero_shot_classification()
    test_batch_embeddings()