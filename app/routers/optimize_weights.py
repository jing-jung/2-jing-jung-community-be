# optimize_weights.py
import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict

# --- 1. 경로 설정 및 데이터 로드 ---
# 이 스크립트 파일의 위치를 기준으로 프로젝트 루트 디렉토리를 찾습니다.
# app/routers -> app -> project_root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))

SHOPS_PATH = os.path.join(PROJECT_ROOT, "shops.csv")
LOGS_PATH = os.path.join(PROJECT_ROOT, "logs.csv")
WEIGHTS_PATH = os.path.join(BASE_DIR, "weights.json")

print("🔍 데이터 로딩 중...")
try:
    shops_df = pd.read_csv(SHOPS_PATH)
    logs_df = pd.read_csv(LOGS_PATH)
    print("✅ 데이터 로드 완료!")
except FileNotFoundError as e:
    print(f"❌ 파일 로드 오류: {e}. 스크립트가 예상하는 파일 위치는 아래와 같습니다:")
    print(f"  - 상점 데이터: {SHOPS_PATH}")
    print(f"  - 로그 데이터: {LOGS_PATH}")
    exit()


# --- 2. MAB(Multi-Armed Bandit) 설정 ---
# 각 '행동(arm)'은 우리가 최적화할 가중치(impression, view, click, bookmark)에 해당합니다.
# 각 행동에 대한 Beta 분포의 파라미터 (alpha, beta)를 저장합니다.
# alpha: 성공(보상) 횟수, beta: 실패 횟수
bandit_params = {
    'impression': {'alpha': 1, 'beta': 1},
    'view': {'alpha': 1, 'beta': 1},
    'click': {'alpha': 1, 'beta': 1},
    'bookmark': {'alpha': 1, 'beta': 1},
}

# --- 3. 시뮬레이션 및 가중치 최적화 ---
print("\n⚙️  피드백 기반 가중치 최적화를 시작합니다 (Thompson Sampling)...")

# 로그 데이터를 세션(session_id)별로 순회하며 시뮬레이션
# 각 세션은 추천 알고리즘을 한 번 테스트하는 독립적인 시도(trial)로 간주합니다.
grouped_logs = logs_df.groupby('session_id')

total_sessions = len(grouped_logs)
for i, (session_id, session_df) in enumerate(grouped_logs):
    print(f"\n--- [세션 {i+1}/{total_sessions}] ---")

    # [Step 1] 현재 Bandit 파라미터에서 가중치 샘플링 (탐색 및 활용)
    # Beta 분포에서 샘플링하여 현재 가장 유망해 보이는 가중치를 선택합니다.
    # 분포가 넓으면(정보 부족) -> 탐색(Exploration)
    # 분포가 좁으면(정보 충분) -> 활용(Exploitation)
    current_weights = {
        action: np.random.beta(params['alpha'], params['beta']) * 10  # 0~1 사이 값을 0~10 스케일로 조정
        for action, params in bandit_params.items()
    }
    current_weights['reservation'] = 100.0  # 예약은 항상 최고점

    print(f"🧪 [테스트 가중치]: impression={current_weights['impression']:.2f}, view={current_weights['view']:.2f}, click={current_weights['click']:.2f}, bookmark={current_weights['bookmark']:.2f}")

    # [Step 2] 샘플링된 가중치로 추천 점수 계산
    # 현재 세션에서 등장한 상점들에 대해 점수를 매깁니다.
    session_shops = session_df['shop_id'].unique()
    scores = defaultdict(float)

    for shop_id in session_shops:
        shop_events = session_df[session_df['shop_id'] == shop_id]['event_type']
        shop_score = sum(current_weights.get(event, 0) for event in shop_events)
        scores[shop_id] = shop_score

    # 점수가 높은 순으로 상점 정렬
    recommended_order = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    
    # [Step 3] 보상(Reward) 측정 및 Bandit 파라미터 업데이트
    # "이 추천이 과연 옳았는가?" -> 현재 세션에서 '예약'이 일어났는지 확인
    # 예약이 일어난 상점이 추천 목록 상위권에 있었다면, 이번 가중치 선택은 '성공'입니다.
    
    # 현재 세션에서 실제 예약이 발생한 상점 찾기
    actual_reservation_shop = session_df[session_df['event_type'] == 'reservation']['shop_id'].iloc[0] if 'reservation' in session_df['event_type'].values else None

    if actual_reservation_shop and actual_reservation_shop in recommended_order:
        # 추천 목록에 예약된 상점이 포함된 경우
        rank = recommended_order.index(actual_reservation_shop)
        
        # 순위가 높을수록 높은 보상 (예: 1등=1, 2등=0.5, 3등=0.25)
        reward = 1 / (rank + 1)
        
        print(f"✅ [성과 측정] '예약' 발생! (추천 순위: {rank+1}등) -> 보상: {reward:.2f}")

        # 이 보상을 기반으로, 이번에 점수를 매기는 데 사용된 행동(가중치)들을 '칭찬'합니다.
        # 즉, 해당 행동들의 Beta 분포 alpha 값을 보상만큼 증가시킵니다.
        events_in_session = session_df[session_df['shop_id'] == actual_reservation_shop]['event_type'].unique()
        for event in events_in_session:
            if event in bandit_params:
                bandit_params[event]['alpha'] += reward # 성공 업데이트
                print(f"  📈 '{event}' 가중치 alpha 증가 -> ({bandit_params[event]['alpha']:.2f}, {bandit_params[event]['beta']:.2f})")

    else:
        # 예약이 없었거나, 추천 목록에 없었다면 '실패'로 간주
        reward = 0
        print("❌ [성과 측정] '예약' 미발생 또는 추천 실패 -> 보상: 0")
        
        # 이번 가중치 조합은 예약으로 이어지지 못했으므로 '벌'을 줍니다.
        # 점수 계산에 기여한 모든 행동들의 Beta 분포 beta 값을 1 증가시킵니다.
        events_in_session = session_df['event_type'].unique()
        for event in events_in_session:
            if event in bandit_params:
                bandit_params[event]['beta'] += 1 # 실패 업데이트
                print(f"  📉 '{event}' 가중치 beta 증가 -> ({bandit_params[event]['alpha']:.2f}, {bandit_params[event]['beta']:.2f})")


# --- 4. 최종 가중치 결정 및 저장 ---
print("\n\n--- [최종 결과] ---")
final_weights = {}
print("📊 최적화된 Bandit 파라미터:")
for action, params in bandit_params.items():
    # 최종 가중치는 각 분포의 기댓값(평균)으로 결정합니다.
    # 기댓값 = alpha / (alpha + beta)
    expected_value = params['alpha'] / (params['alpha'] + params['beta'])
    final_weights[action] = round(expected_value * 10, 2) # 0~10 스케일로 조정
    print(f"  - {action}: alpha={params['alpha']:.2f}, beta={params['beta']:.2f} -> 최종 가중치: {final_weights[action]}")

final_weights['reservation'] = 100.0

print(f"\n✅ 최적화 완료! 최종 가중치를 {WEIGHTS_PATH} 에 저장합니다.")
print(f"   (가중치: {final_weights})")

with open(WEIGHTS_PATH, "w", encoding="utf-8") as f:
    json.dump(final_weights, f, indent=4)

print("\n🎉 모든 과정이 성공적으로 완료되었습니다!")