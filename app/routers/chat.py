import pandas as pd
import urllib.parse
import os
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

router = APIRouter()

# 2. 모델 초기화
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.5,
    api_key=os.getenv("GROQ_API_KEY")
)


class ChatRequest(BaseModel):
    user_id: str
    message: str


class SearchIntent(BaseModel):
    region: str = Field(default="")
    category: str = Field(default="")
    intent_keyword: str = Field(default="")


# 프롬프트 설정
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", "사용자의 질문이 식당 추천과 관련이 있는지 판별해. 관련이 없다면 REJECT, 있다면 ACCEPT를 출력해."),
    ("user", "{message}")
])
intent_chain = intent_prompt | llm | StrOutputParser()

extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """사용자의 질문에서 지역, 음식종류, 상황의도를 추출해. 
    [🔥 중요 규칙]
    1. 지역(region): '역', '구', '동', '쪽', '근처' 등의 꼬리표는 무조건 떼어내고 '핵심 지명'만 추출해. 
       (예: '강남구' -> '강남', '강남역' -> '강남', '홍대입구역' -> '홍대', '가산디지털단지' -> '가산')
       만약 질문에 지역 정보가 아예 없으면 빈 문자열("")을 넣어줘.
    2. 음식종류(category): '파스타', '고기', '카페' 등 명확한 명사만 추출해.
    3. 상황의도(intent_keyword): '데이트', '가성비' 등 목적에 맞는 명사만 추출해."""),
    ("user", "{message}")
])
extraction_chain = extraction_prompt | llm.with_structured_output(SearchIntent)

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 동물의 숲의 친절하고 사랑스러운 안내원 '여울'이야! 🌳
    항상 밝고 귀여운 말투(~예용, ~랍니다!, ~어떨까요?)를 써줘.
    대답의 첫 시작은 무조건 자연스러운 인사말(예: "안녕하세요! 원하시는 곳을 찾아드릴게용!")로 시작해. '예요!' 처럼 중간부터 말하지 마.

    [출력 형식 규칙 - 무조건 지킬 것]
    - 식당 이름에 **(별표)를 써서 강조하지 마.
    - 각 식당마다 번호를 매기고, 이름/주소/링크를 반드시 아래의 [올바른 답변 예시]와 똑같은 줄바꿈 형식으로 출력해.

    [올바른 답변 예시]
    원하시는 맛집을 제가 딱 찾아왔어용!

    1. 매쎄 Mésse - 분위기 좋은 식당이랍니다!
    주소: 서울 강남구 논현로32길 5 101호
    카카오맵 링크: https://map.kakao.com/link/search/...

    2. 도시문 - 디저트를 즐기기 좋은 곳이에용!
    주소: 서울특별시 강남구 남부순환로351길 4 도곡동 지하 1층
    카카오맵 링크: https://map.kakao.com/link/search/...

    마음에 드시는 곳이 있으면 좋겠네요! 또 궁금한 거 있으시면 언제든 말씀해주세용!

    [추천 식당 데이터]
    {recommendation}"""),
    ("user", "{message}")
])
answer_chain = answer_prompt | llm | StrOutputParser()


# 3. 클래스 정의
class RecommendationEngine:
    def __init__(self, shops_path: str, logs_path: str):
        self.shops_df = pd.read_csv(shops_path)
        self.logs_df = pd.read_csv(logs_path)
        self._preprocess_data()

    def _preprocess_data(self):
        self.logs_df = self.logs_df.sort_values(by=['session_id', 'event_timestamp'])
        self.logs_df['search_query'] = self.logs_df.groupby('session_id')['search_query'].ffill()
        weights = {'impression': 1, 'click': 2, 'view': 3, 'bookmark': 10, 'reservation': 20}
        self.logs_df['score'] = self.logs_df['event_type'].map(weights).fillna(0)
        self.shop_scores = self.logs_df.groupby(['shop_id', 'search_query'])['score'].sum().reset_index()

    def get_recommendation(self, region: str, category: str, intent_keyword: str) -> list:
        filtered_shops = self.shops_df[
            (self.shops_df['address'].fillna('').str.contains(region)) &
            (self.shops_df['categories'].fillna('').str.contains(category))
            ].copy()

        if filtered_shops.empty:
            return []

        relevant_scores = self.shop_scores[
            self.shop_scores['search_query'].fillna('').str.contains(intent_keyword)
        ]
        merged_df = pd.merge(filtered_shops, relevant_scores, on='shop_id', how='left')
        merged_df['score'] = merged_df['score'].fillna(0)
        ranked_shops = merged_df.sort_values(by='score', ascending=False)

        top_3 = ranked_shops.head(3)
        result = []
        for _, row in top_3.iterrows():
            encoded_name = urllib.parse.quote(row['shop_name'])
            map_url = f"https://map.kakao.com/link/search/{encoded_name}"

            result.append({
                "name": row['shop_name'],
                "address": row['address'],
                "map_link": map_url
            })
        return result

    def evaluate_performance(self, k=3):
        true_likes = self.shop_scores[self.shop_scores['score'] >= 10].groupby('search_query')['shop_id'].apply(list).to_dict()
        
        if not true_likes:
            return {"message": "평가할 정답 데이터(북마크/예약 로그)가 부족합니다."}

        precisions, recalls, ndcgs = [], [], []

        for query, true_items in true_likes.items():
            relevant_scores = self.shop_scores[self.shop_scores['search_query'].fillna('').str.contains(query, regex=False)]
            merged_df = pd.merge(self.shops_df, relevant_scores, on='shop_id', how='left')
            merged_df['score'] = merged_df['score'].fillna(0)
            
            top_k_shops = merged_df.sort_values(by='score', ascending=False).head(k)['shop_id'].tolist()
            hits = len(set(top_k_shops) & set(true_items))
            
            precisions.append(hits / k)
            recalls.append(hits / len(true_items) if len(true_items) > 0 else 0)
            
            dcg = sum([1 / np.log2(i + 2) for i, shop in enumerate(top_k_shops) if shop in true_items])
            idcg = sum([1 / np.log2(i + 2) for i in range(min(len(true_items), k))])
            ndcgs.append(dcg / idcg if idcg > 0 else 0)

        return {
            "Precision_at_3": round(np.mean(precisions), 4),
            "Recall_at_3": round(np.mean(recalls), 4),
            "NDCG_at_3": round(np.mean(ndcgs), 4),
            "Tested_Queries": len(true_likes)
        }


# 4. 추천 엔진 초기화
engine = None
try:
    shops_path = "shops.csv"
    logs_path = "logs.csv"
    if os.path.exists(shops_path) and os.path.exists(logs_path):
        engine = RecommendationEngine(shops_path, logs_path)
except Exception:
    pass


# 5. API 라우터
@router.get("/chat/test")
def test_connection():
    return {"status": "ok", "message": "채팅 라우터 연결 성공!"}


@router.get("/chat/evaluate")
def evaluate_model():
    if engine is None:
        return {"error": "추천 엔진이 초기화되지 않았습니다."}
    return engine.evaluate_performance()


@router.post("/chat")
async def chat_with_bot(req: ChatRequest):
    if engine is None:
        return {"reply": "앗, 서버의 장부(데이터)를 읽어오지 못했어요. 잠시만 기다려 주세요! 😭"}

    intent_check = await intent_chain.ainvoke({"message": req.message})
    if "REJECT" in intent_check:
        return {"reply": "안녕하세요! 저는 식당 추천을 도와드리는 안내원 여울이에용. 식당과 관련된 질문을 해주시면 친절하게 안내해 드릴게요! 🏕️"}

    extracted = await extraction_chain.ainvoke({"message": req.message})

    recommendation_data = engine.get_recommendation(
        region=extracted.region,
        category=extracted.category,
        intent_keyword=extracted.intent_keyword
    )

    if not recommendation_data:
        return {"reply": "앗, 죄송해용! 마을 장부에서 조건에 딱 맞는 식당을 찾지 못했어요 ㅠㅠ 다른 동네나 메뉴로 다시 물어봐 주실래요?"}

    final_answer = await answer_chain.ainvoke({
        "recommendation": str(recommendation_data),
        "message": req.message
    })
    return {"reply": final_answer}