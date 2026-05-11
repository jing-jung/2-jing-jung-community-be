# terminal_debug.py
import asyncio
import urllib.parse
import pandas as pd
# 기존 라우터에서 필요한 모듈만 임포트
from app.routers.chat import intent_chain, extraction_chain, answer_chain, engine


async def run_terminal():
    print("=" * 60)
    print("🏕️ 여울이의 마을 맛집 안내소 - 터미널 디버깅 모드 🏕️")
    print("   (채팅을 종료하려면 'q' 또는 'quit'를 입력하세요)")
    print("=" * 60)

    user_memory = {"exclude_keyword": ""}

    if engine is None:
        print("⚠️ 에러: 추천 엔진이 초기화되지 않았습니다. (shops.csv, logs.csv 확인 필요)")
        return

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

        # [Step 2] 위치 및 알러지 필터링 (엔진 내부 로직 디버깅)
        filtered_shops = engine.shops_df.copy()
        if extracted.region:
            filtered_shops = filtered_shops[
                filtered_shops['address'].fillna('').str.contains(extracted.region, regex=False)]

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

        # ------------------- 수정할 부분 시작 -------------------
        # [Step 3] 카테고리/메뉴 매칭 (상황 키워드인 intent_keyword는 제외!)
        if extracted.category:  
            combined_info = filtered_shops['categories'].fillna('') + " " + \
                            filtered_shops['menus'].fillna('') + " " + \
                            filtered_shops['facilities'].fillna('')
            
            # 카테고리(예: 파스타, 카페)만 텍스트 매칭에 사용
            mask = combined_info.str.contains(extracted.category, regex=True)
            temp_filtered = filtered_shops[mask]
            
            # 안전장치: 필터링 했더니 0개가 되면, 너무 조건이 빡빡한 것이므로 필터링 전 상태 유지
            if not temp_filtered.empty:
                filtered_shops = temp_filtered
            else:
                print(f"⚠️ [Step 3] '{extracted.category}' 필터링 시 0개가 되어 필터링을 생략합니다.")
                
        print(f"[Step 3] 카테고리 매칭 완료 -> 남은 후보 {len(filtered_shops)}개")
        # ------------------- 수정할 부분 끝 -------------------

        if filtered_shops.empty:
            print("Bot: 키워드 매칭 후 조건에 맞는 식당이 없습니다.")
            continue

        # [Step 4] 스코어링
        relevant_scores = engine.shop_scores[
            engine.shop_scores['search_query'].fillna('').str.contains(
                extracted.intent_keyword if extracted.intent_keyword else ' ', regex=False)
        ]

        merged_df = pd.merge(filtered_shops, relevant_scores, on='shop_id', how='left')
        merged_df['score'] = merged_df['score'].fillna(0)
        merged_df = merged_df.drop_duplicates(subset=['shop_id'])
        ranked_shops = merged_df.sort_values(by='score', ascending=False)

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