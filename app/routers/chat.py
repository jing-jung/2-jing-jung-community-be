import pandas as pd
import urllib.parse
from fastapi import APIRouter
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

router = APIRouter()

# OpenAI 모델 초기화 (API 키는 환경변수에 설정되어 있어야 해)
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5) # 창의적인 말투를 위해 온도를 살짝 올림

class ChatRequest(BaseModel):
    user_id: str
    message: str

class SearchIntent(BaseModel):
    region: str = Field(default="")
    category: str = Field(default="")
    intent_keyword: str = Field(default="")

# 1. 의도 파악 프롬프트 (그대로 유지)
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", "사용자의 질문이 식당 추천과 관련이 있는지 판별해. 관련이 없다면 REJECT, 있다면 ACCEPT를 출력해."),
    ("user", "{message}")
])
intent_chain = intent_prompt | llm | StrOutputParser()

# 2. 키워드 추출 프롬프트 (그대로 유지)
extraction_prompt = ChatPromptTemplate.from_messages([
    ("system", "사용자의 질문에서 지역, 음식종류, 상황의도를 추출해. 정보가 없으면 빈 문자열을 넣어줘."),
    ("user", "{message}")
])
extraction_chain = extraction_prompt | llm.with_structured_output(SearchIntent)

# 3. 여울이 컨셉 답변 생성 프롬프트 (수정됨)
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """너는 우리 마을의 친절한 안내원 '여울'이야! 
    동물의 숲 주민에게 말하듯이 항상 밝고 친절하며 귀여운 말투(~예용, ~어떨까요?, ~랍니다! 등)를 사용해줘.
    다음 제공된 식당 정보를 바탕으로 사용자에게 딱 맞는 식당을 추천해줘.
    응답의 마지막에는 반드시 내가 제공한 '카카오맵 링크'를 함께 알려줘.
    
    추천 식당 정보: {recommendation}"""),
    ("user", "{message}")
])
answer_chain = answer_prompt | llm | StrOutputParser()

class RecommendationEngine:
    def __init__(self, shops_path: str, logs_path: str):
        self.shops_df = pd.read_csv(shops_path)
        self.logs_df = pd.read_csv(logs_path)
        self._preprocess_data()

    def _preprocess_data(self):
        # 세션별로 빈 검색어 채우기 및 점수 계산 로직
        self.logs_df = self.logs_df.sort_values(by=['session_id', 'event_timestamp'])
        self.logs_df['search_query'] = self.logs_df.groupby('session_id')['search_query'].ffill()
        weights = {'impression': 1, 'click': 2, 'view': 3, 'bookmark': 10, 'reservation': 20}
        self.logs_df['score'] = self.logs_df['event_type'].map(weights).fillna(0)
        self.shop_scores = self.logs_df.groupby(['shop_id', 'search_query'])['score'].sum().reset_index()

    def get_recommendation(self, region: str, category: str, intent_keyword: str) -> list:
        # 필터링 로직
        filtered_shops = self.shops_df[
            (self.shops_df['address'].fillna('').str.contains(region)) &
            (self.shops_df['categories'].fillna('').str.contains(category))
        ].copy()
        
        if filtered_shops.empty:
            return []
            
        # 랭킹 계산
        relevant_scores = self.shop_scores[
            self.shop_scores['search_query'].fillna('').str.contains(intent_keyword)
        ]
        merged_df = pd.merge(filtered_shops, relevant_scores, on='shop_id', how='left')
        merged_df['score'] = merged_df['score'].fillna(0)
        ranked_shops = merged_df.sort_values(by='score', ascending=False)
        
        top_3 = ranked_shops.head(3)
        result = []
        for _, row in top_3.iterrows():
            # 카카오맵 검색 URL 생성
            encoded_name = urllib.parse.quote(row['shop_name'])
            map_url = f"https://map.kakao.com/link/search/{encoded_name}"
            
            result.append({
                "name": row['shop_name'],
                "address": row['address'],
                "map_link": map_url
            })
        return result

# 서버 시작 시 데이터 로드
engine = RecommendationEngine('shops.csv', 'logs.csv')

@router.post("/chat")
async def chat_with_bot(req: ChatRequest):
    # 1. 의도 파악 (가드레일)
    intent_check = await intent_chain.ainvoke({"message": req.message})
    if "REJECT" in intent_check:
        return {"reply": "안녕하세요! 저는 식당 추천을 도와드리는 안내원 여울이에용. 식당과 관련된 질문을 해주시면 친절하게 안내해 드릴게요! 🏕️"}

    # 2. 키워드 추출
    extracted = await extraction_chain.ainvoke({"message": req.message})

    # 3. 데이터 기반 추천 식당 검색
    recommendation_data = engine.get_recommendation(
        region=extracted.region,
        category=extracted.category,
        intent_keyword=extracted.intent_keyword
    )

    if not recommendation_data:
         return {"reply": "앗, 죄송해용! 마을 장부에서 조건에 딱 맞는 식당을 찾지 못했어요 ㅠㅠ 다른 동네나 메뉴로 다시 물어봐 주실래요?"}

    # 4. 여울이 말투로 최종 응답 생성
    final_answer = await answer_chain.ainvoke({
        "recommendation": str(recommendation_data),
        "message": req.message
    })
    return {"reply": final_answer}
