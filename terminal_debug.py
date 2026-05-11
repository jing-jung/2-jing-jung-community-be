# terminal_debug.py
import asyncio
import urllib.parse
import pandas as pd
import os
# 기존 라우터에서 필요한 모듈만 임포트
from app.routers.chat import intent_chain, extraction_chain, answer_chain, RecommendationEngine


async def run_terminal():
    print("=" * 60)
    print("🏕️ 여울이의 마을 맛집 안내소 - 터미널 디버깅 모드 🏕️")
    print("   (채팅을 종료하려면 'q' 또는 'quit'를 입력하세요)")
    print("=" * 60)

    # --- 경로 수정 ---
    # 스크립트 실행 위치와 관계없이 프로젝트 루트를 기준으로 파일 경로를 설정
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    SHOPS_PATH = os.path.join(PROJECT_ROOT, "shops.csv")
    LOGS_PATH = os.path.join(PROJECT_ROOT, "logs.csv")

    engine = None
    try:
        if os.path.exists(SHOPS_PATH) and os.path.exists(LOGS_PATH):
            engine = RecommendationEngine(shops_path=SHOPS_PATH, logs_path=LOGS_PATH)
    except Exception as e:
        print(f"엔진 초기화 중 오류 발생: {e}")

    if engine is None:
        print("⚠️ 에러: 추천 엔진이 초기화되지 않았습니다. (shops.csv, logs.csv 확인 필요)")
        print(f"  - 상점 데이터 경로: {SHOPS_PATH}")
        print(f"  - 로그 데이터 경로: {LOGS_PATH}")
        return
    # --- 경로 수정 끝 ---

    user_memory = {"exclude_keyword": ""}

    while True:
        message = input("\nYou: ")
        if message.lower() in ['q', 'quit']:
            break

        # [디버깅] 인텐트 필터링
        intent_check = await intent_chain.ainvoke({"message": message})
        if "REJECT" in intent_check:
            print("Bot: 식당과 관련된 질문이 아닙니다.")
            continue

        # [Step 1] 엔티티 추출 완료
        extracted = await extraction_chain.ainvoke({"message": message})

        # 기억 업데이트 로직
        if extracted.exclude_keyword:
            user_memory["exclude_keyword"] = extracted.exclude_keyword
        else:
            extracted.exclude_keyword = user_memory["exclude_keyword"]

        print(
            f"\n[Step 1] 추출 결과: location='{extracted.region}', categories='{extracted.category}', situations='{extracted.intent_keyword}', exclude='{extracted.exclude_keyword}'")

        # [Step 2] 위치 및 알러지 필터링
        filtered_shops = engine.shops_df.copy()
        
        # 장소를 명확히 말했을 때만 필터링 (다 강남이면 어차피 통과)
        if extracted.region:
            filtered_shops = filtered_shops[filtered_shops['address'].fillna('').str.contains(extracted.region,
 regex=False)]
        
        # 알러지 필터링은 건강과 직결되므로 엄격하게 유지!
        if extracted.exclude_keyword:
            exclude_mask = ~(
                filtered_shops['categories'].fillna('').str.contains(extracted.exclude_keyword, regex=True) |
                filtered_shops['menus'].fillna('').str.contains(extracted.exclude_keyword, regex=True)
            )
            filtered_shops = filtered_shops[exclude_mask]

        print(f"[Step 2] 후보 {len(filtered_shops)}개 (위치 및 제외 키워드 필터링 적용 후)")

        if filtered_shops.empty:
            print("Bot: 조건에 맞는 식당이 장부에 하나도 없습니다 ㅠㅠ")
            continue

        # [Step 4] 바로 스코어링으로 넘어가기 (LTR의 힘을 믿으세요)
        search_intent = f"{extracted.category} {extracted.intent_keyword}".strip()
        
        if search_intent:
            relevant_scores = engine.shop_scores[
                engine.shop_scores['search_query'].fillna('').str.contains(search_intent, regex=False)
            ]
        else:
            relevant_scores = engine.shop_scores

        merged_df = pd.merge(filtered_shops, relevant_scores, on='shop_id', how='left')
        merged_df['score'] = merged_df['score'].fillna(0)
        
        if search_intent and merged_df['score'].sum() == 0:
            print(f"⚠️ '{search_intent}'에 대한 기록된 점수가 없어, 키워드 매칭으로 기본 점수(+10)를 부여합니다.")
            keyword_mask = merged_df['categories'].fillna('') + " " + merged_df['menus'].fillna('')
            merged_df.loc[keyword_mask.str.contains(search_intent.replace(" ", "|"), regex=True), 'score'] += 10.0

        merged_df = merged_df.drop_duplicates(subset=['shop_id'])
        ranked_shops = merged_df.sort_values(by='score', ascending=False)

        if ranked_shops.empty:
            print("Bot: 스코어링 후 조건에 맞는 식당이 없습니다.")
            continue

        print(
            f"[Step 4] 스코어 예측 완료 - score min={ranked_shops['score'].min():.4f}, max={ranked_shops['score'].max():.4f}, mean={ranked_shops['score'].mean():.4f}")

        # [Step 5] 상위 10개 출력 (터미널용)
        top_k = ranked_shops.head(10)
        print(f"[Step 5] 상위 10개 랭킹:")
        for i, (_, row) in enumerate(top_k.iterrows()):
            print(f"    {i + 1}. {row['shop_name'][:15]:<15} (score={row['score']:.4f})")

        # [Step 6] 챗봇(LLM) 최종 응답 생성
        top_3 = ranked_shops.head(3)
        formatted_reco = ""
        for i, (_, row) in enumerate(top_3.iterrows()):
            encoded_name = urllib.parse.quote(row['shop_name'])
            map_link = f"https://map.kakao.com/link/search/{encoded_name}"
            formatted_reco += f"\n{i + 1}. {row['shop_name']}\n주소: {row['address']}\n카카오맵 링크: {map_link}\n"

        print("\nBot (여울이) 응답 생성 중...\n")
        final_answer = await answer_chain.ainvoke({
            "recommendation": formatted_reco,
            "message": message
        })
        print(f"Bot:\n{final_answer}\n")


if __name__ == "__main__":
    # Windows 환경에서 asyncio 에러 방지
    import sys

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(run_terminal())