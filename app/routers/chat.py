import pandas as pd
import urllib.parse
import os
import numpy as np
import json
import traceback
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import asyncio
from cachetools import TTLCache
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

router = APIRouter()

# 2. 모델 초기화
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
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
    exclude_keyword: str = Field(default="")


# 프롬프트 설정
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", "사용자의 질문이 식당 추천과 관련이 있는지 판별해. 관련이 없다면 REJECT, 있다면 ACCEPT를 출력해."),
    ("user", "{message}")
])
intent_chain = intent_prompt | llm | StrOutputParser()

extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", """당신은 눈치가 아주 빠른 맛집 추천 어시스턴트입니다. 
    사용자의 입력에서 다음 정보를 추출하되, 주어진 텍스트를 그대로 뽑지 말고 '의도'를 파악해 변환하세요.

    [🔥 중요 규칙]
    1. 지역(region): '역', '구', '동', '쪽', '근처' 등의 꼬리표는 무조건 떼어내고 '핵심 지명'만 추출해. 
       (예: '강남구' -> '강남', '강남역' -> '강남'). 정보가 없으면 절대 억지로 만들지 말고 빈 문자열("")을 넣어.

    2. 음식종류(category) - ★[자동 추론 필수]★: 
       사용자가 "싱싱한", "매콤한", "비오는 날", "스트레스 받는" 처럼 추상적인 느낌이나 형용사를 입력하면, 
       어떤 음식을 먹고 싶은 것인지 스스로 판단해서 실제 '음식 카테고리 명사'로 변환해!
       (예: "싱싱한 거" -> "해산물|회|초밥", "매콤한 거" -> "마라탕|매운|낙지")

    3. 상황의도(intent_keyword): '데이트', '가성비', '어버이날' 등 목적에 맞는 명사를 추출해. 
       만약 "조용한" 이라면 식당 특징인 "룸|프라이빗" 등으로 변환해서 추출해. (정보 없으면 "")

    4. 제외키워드(exclude_keyword): 알러지나 '제외', '빼고', '말고' 등의 표현이 있으면 피해야 할 재료를 추출해.
       - 꿀팁: '해산물 알러지'면 파이썬이 찾기 쉽게 '해물|해산물|회|초밥|일식' 처럼 파이프(|) 기호로 묶어줘.
       - '파스타 말고' 이면 '파스타'를 넣어줘. (없으면 무조건 "")
    """),
    ("user", "{message}")
])

extraction_chain = extraction_prompt | llm.with_structured_output(SearchIntent)

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 동물의 숲의 친절하고 사랑스러운 안내원 '여울'이야! 🌳
    항상 밝고 귀여운 말투(~예용, ~랍니다!, ~어떨까요?)를 써줘.
    대답의 첫 시작은 무조건 자연스러운 인사말(예: "안녕하세요! 원하시는 곳을 찾아드릴게용!")로 시작해. '예요!' 처럼 중간부터 말하지 마.

    [출력 형식 규칙 - 무조건 지킬 것]
    식당 이름에 **(별표)를 써서 강조하지 마.
    내가 전달해주는 [추천 식당 데이터]를 바탕으로, 각 식당마다 무조건 번호를 매기고
    식당 정보가 끝날 때마다 반드시 엔터를 두 번 쳐서(한 줄 띄어쓰기) 다음 식당과 완벽하게 분리해.
    지도 링크 바로 옆에 다음 식당 이름을 붙여 쓰면 절대 안 돼!

    [올바른 답변 예시]
    원하시는 맛집을 제가 딱 찾아왔어용!

    1. 매쎄 Mésse - 분위기 좋은 식당이랍니다!
    주소: 서울 강남구 논현로32길 5 101호
    카카오맵 링크: https://map.kakao.com/link/search/...

    2. 도시문 - 디저트를 즐기기 좋은 곳이에용!
    주소: 서울특별시 강남구 남부순환로351길 4 도곡동 지하 1층
    카카오맵 링크: https://map.kakao.com/link/search/...
    (👈 여기에 반드시 띄어쓰기 두 줄 해줘)
    마음에 드시는 곳이 있으면 좋겠네요! 또 궁금한 거 있으시면 언제든 말씀해주세용!

    [추천 식당 데이터]
    {recommendation}"""),
    ("user", "{message}")
])
answer_chain = answer_prompt | llm | StrOutputParser()

# 3. 클래스 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class RecommendationEngine:
    def __init__(self, shops_path: str, logs_path: str):
        self.shops_df = pd.read_csv(shops_path)
        self.logs_df = pd.read_csv(logs_path)
        self._preprocess_data()

    def _preprocess_data(self):
        weights_path = os.path.join(BASE_DIR, "weights.json")
        if os.path.exists(weights_path):
            with open(weights_path, "r") as f:
                weights = json.load(f)
        else:
            # 파일이 없을 때를 대비한 기본값
            weights = {'impression': 0.2, 'view': 3.4, 'click': 2.3, 'bookmark': 2.8, 'reservation': 100.0}

        self.logs_df = self.logs_df.sort_values(by=['session_id', 'event_timestamp'])
        self.logs_df['search_query'] = self.logs_df.groupby('session_id')['search_query'].ffill()
        self.logs_df['score'] = self.logs_df['event_type'].map(weights).fillna(0)
        self.shop_scores = self.logs_df.groupby(['shop_id', 'search_query'])['score'].sum().reset_index()

    def get_recommendation(self, region: str, category: str, intent_keyword: str, exclude_keyword: str = "") -> list:
        # [Step 2] 위치 및 알러지 필터링
        filtered_shops = self.shops_df.copy()
        
        # 장소를 명확히 말했을 때만 필터링 (다 강남이면 어차피 통과)
        if region:
            filtered_shops = filtered_shops[filtered_shops['address'].fillna('').str.contains(region, regex=False)]
        
        # 알러지 필터링은 건강과 직결되므로 엄격하게 유지!
        if exclude_keyword:
            exclude_mask = ~(
                filtered_shops['categories'].fillna('').str.contains(exclude_keyword, regex=True) |
                filtered_shops['menus'].fillna('').str.contains(exclude_keyword, regex=True)
            )
            filtered_shops = filtered_shops[exclude_mask]

        if filtered_shops.empty: return []

        # [Step 4] 바로 스코어링으로 넘어가기
        search_intent = f"{category} {intent_keyword}".strip()
        
        if search_intent:
            relevant_scores = self.shop_scores[
                self.shop_scores['search_query'].fillna('').str.contains(search_intent, regex=False)
            ]
        else:
            relevant_scores = self.shop_scores

        merged_df = pd.merge(filtered_shops, relevant_scores, on='shop_id', how='left')
        merged_df['score'] = merged_df['score'].fillna(0)
        
        if search_intent and merged_df['score'].sum() == 0:
            keyword_mask = merged_df['categories'].fillna('') + " " + merged_df['menus'].fillna('')
            merged_df.loc[keyword_mask.str.contains(search_intent.replace(" ", "|"), regex=True), 'score'] += 10.0

        merged_df = merged_df.drop_duplicates(subset=['shop_id'])
        ranked_shops = merged_df.sort_values(by='score', ascending=False)
        
        if ranked_shops.empty: return []

        top_3 = ranked_shops.head(3)
        result = []
        for _, row in top_3.iterrows():
            encoded_name = urllib.parse.quote(row['shop_name'])
            result.append({
                "name": row['shop_name'],
                "address": row['address'],
                "map_link": f"https://map.kakao.com/link/search/{encoded_name}"
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


# 4. 추천 엔진 초기화 (전역 변수)
engine = None


async def init_recommendation_engine():
    """
    추천 엔진 초기화 (서버 시작 시 한 번만 실행)
    FastAPI lifespan에서 호출
    """
    global engine
    try:
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        shops_path = os.path.join(PROJECT_ROOT, "shops.csv")
        logs_path = os.path.join(PROJECT_ROOT, "logs.csv")
        
        print("="*50)
        print(" FastAPI 서버 시작: 추천 엔진 초기화 시도")
        print(f" - 프로젝트 루트: {PROJECT_ROOT}")
        print(f" - 상점 데이터 경로: {shops_path}")
        print(f" - 로그 데이터 경로: {logs_path}")

        if os.path.exists(shops_path) and os.path.exists(logs_path):
            engine = RecommendationEngine(shops_path, logs_path)
            print(" ✅ 추천 엔진이 성공적으로 초기화되었습니다.")
        else:
            print(" ❌ 에러: 'shops.csv' 또는 'logs.csv' 파일을 찾을 수 없습니다.")
            engine = None
        print("="*50)

    except Exception as e:
        print(f" ❌❌❌ 추천 엔진 초기화 중 심각한 오류 발생: {e}")
        print(traceback.format_exc())
        engine = None

# 5. API 라우터
@router.get("/chat/test")
def test_connection():
    return {"status": "ok", "message": "채팅 라우터 연결 성공!"}


@router.get("/chat/evaluate")
def evaluate_model():
    if engine is None:
        return {"error": "추천 엔진이 초기화되지 않았습니다."}
    return engine.evaluate_performance()


# 메모리 누수 방지: TTL 캐시 사용 (30분 후 자동 삭제)
user_memory = TTLCache(maxsize=10000, ttl=1800)


@router.post("/chat")
async def chat_with_bot(req: ChatRequest):
    if engine is None:
        return {"reply": "앗, 서버의 장부(데이터)를 읽어오지 못했어요. 잠시만 기다려 주세요! 😭"}
    
    if not llm or not intent_chain:
        return {"reply": "죄송합니다. AI 챗봇 기능이 현재 비활성화되어 있습니다. GROQ_API_KEY를 설정해주세요."}

    intent_check = await intent_chain.ainvoke({"message": req.message})
    if "REJECT" in intent_check:
        return {"reply": "안녕하세요! 저는 식당 추천을 도와드리는 안내원 여울이에용. 식당과 관련된 질문을 해주시면 친절하게 안내해 드릴게요! 🏕️"}

    extracted = await extraction_chain.ainvoke({"message": req.message})

    # 🧠 [선택적 기억 장치: 알러지는 평생 기억, 나머지는 쿨하게 잊기]
    if req.user_id not in user_memory:
        user_memory[req.user_id] = {"exclude_keyword": "", "region": ""}

    # 1. 알러지/제외 (Hard Constraint): 생명과 직결되니 무조건 '누적'해서 평생 기억!
    if extracted.exclude_keyword:
        old_exclude = user_memory[req.user_id]["exclude_keyword"]
        new_exclude = f"{old_exclude}|{extracted.exclude_keyword}".strip("|") if old_exclude else extracted.exclude_keyword
        user_memory[req.user_id]["exclude_keyword"] = new_exclude
        extracted.exclude_keyword = new_exclude
    else:
        extracted.exclude_keyword = user_memory[req.user_id].get("exclude_keyword", "")

    # 2. 지역 (UX 편의): 매번 "강남" 치기 귀찮으니 기억하되, 다른 동네 말하면 쿨하게 덮어쓰기!
    if extracted.region:
        user_memory[req.user_id]["region"] = extracted.region
    else:
        extracted.region = user_memory[req.user_id].get("region", "")

    # 3. 메뉴(category) & 목적(intent): 기억 안 함! ❌

    recommendation_data = engine.get_recommendation(
        region=extracted.region,
        category=extracted.category,
        intent_keyword=extracted.intent_keyword,
        exclude_keyword=extracted.exclude_keyword
    )

    if not recommendation_data:
        return {"reply": "앗, 죄송해용! 마을 장부에서 조건에 딱 맞는 식당을 찾지 못했어요 ㅠㅠ 다른 동네나 메뉴로 다시 물어봐 주실래요?"}

    formatted_reco = ""
    for i, item in enumerate(recommendation_data):
        formatted_reco += f"\n{i+1}. {item['name']}\n주소: {item['address']}\n카카오맵 링크: {item['map_link']}\n"
    
    final_answer = await answer_chain.ainvoke({
        "recommendation": formatted_reco,
        "message": req.message
    })
    return {"reply": final_answer}