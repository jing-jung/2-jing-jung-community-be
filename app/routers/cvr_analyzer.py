import pandas as pd
import os
import json

# 1. 파일 경로 설정 (프로젝트 루트 경로 기준으로 변경)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR)) # app/routers -> app -> project root
logs_path = os.path.join(PROJECT_ROOT, "logs.csv")


print("🔍 데이터 분석을 시작합니다... (logs.csv 읽는 중)")
logs_df = pd.read_csv(logs_path)

# 2. 세션(session_id)과 식당(shop_id) 단위로 유저가 무슨 행동을 했는지 묶기
# 예: 세션 A가 식당 B에서 [click, bookmark, reservation] 을 했음을 집합(set)으로 만듭니다.
action_grouped = logs_df.groupby(['session_id', 'shop_id'])['event_type'].apply(set).reset_index()

# 3. 분석할 행동 리스트
actions = ['impression', 'view', 'click', 'bookmark']
cvr_results = {}

# 4. 각 행동별로 '예약(reservation)'으로 이어진 비율(CVR) 계산
for action in actions:
    # 해당 행동(action)을 한 케이스만 필터링
    action_cases = action_grouped[action_grouped['event_type'].apply(lambda x: action in x)]
    total_action_count = len(action_cases)

    # 그 중에서 'reservation'도 같이 일어난(예약까지 간) 케이스 찾기
    reservation_cases = action_cases[action_cases['event_type'].apply(lambda x: 'reservation' in x)]
    converted_count = len(reservation_cases)

    # CVR(전환율) 퍼센트 계산
    if total_action_count > 0:
        cvr = (converted_count / total_action_count) * 100
    else:
        cvr = 0.0

    cvr_results[action] = cvr

# 5. 결과 출력 (보고서에 들어갈 핵심 데이터!)
print("\n📊 --- 데이터 기반 CVR (예약 전환율) 분석 결과 --- 📊")
for action, cvr in cvr_results.items():
    print(f"🔸 {action.upper()} ➔ 예약 전환율: {cvr:.2f}%")

print("\n💡 [추천 가중치 세팅 가이드]")
print("예약(reservation)의 가중치를 100점으로 두었을 때, 데이터가 증명한 가장 이상적인 가중치는 아래와 같습니다.")

new_weights = {}
for action, cvr in cvr_results.items():
    new_weights[action] = round(cvr, 1)  # 소수점 1자리까지 반올림해서 점수로 사용!
new_weights['reservation'] = 100.0  # 예약은 최종 목표니까 100점 만점!

print(f"✅ weights = {new_weights}")
print("--------------------------------------------------")

# 6. weights.json 파일로 저장
weights_path = os.path.join(BASE_DIR, "weights.json")
with open(weights_path, "w", encoding="utf-8") as f:
    json.dump(new_weights, f, indent=4)

print(f"✅ 새로운 가중치가 {weights_path}에 저장되었습니다!")