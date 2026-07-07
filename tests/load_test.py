"""
Performance & Load Testing Script
Locust를 사용한 부하 테스트
"""
from locust import HttpUser, task, between
import random
import json


class CommunityUser(HttpUser):
    """커뮤니티 플랫폼 사용자 시뮬레이션"""
    
    wait_time = between(1, 3)  # 요청 간 1-3초 대기
    
    def on_start(self):
        """테스트 시작 시 로그인"""
        self.login()
    
    def login(self):
        """로그인 수행"""
        response = self.client.post("/users/login", json={
            "email": f"test{random.randint(1, 100)}@example.com",
            "password": "test1234"
        })
        
        if response.status_code == 200:
            # 세션 ID 저장
            self.session_id = response.cookies.get("session_id")
    
    @task(5)  # 가중치 5
    def view_posts(self):
        """게시글 목록 조회 (가장 빈번한 요청)"""
        offset = random.randint(0, 100)
        self.client.get(f"/posts?offset={offset}&limit=10")
    
    @task(3)
    def view_post_detail(self):
        """게시글 상세 조회"""
        post_id = random.randint(1, 1000)
        self.client.get(f"/posts/{post_id}")
    
    @task(2)
    def create_post(self):
        """게시글 작성"""
        self.client.post("/posts", data={
            "title": f"Test Post {random.randint(1, 10000)}",
            "content": "This is a test post content for load testing"
        })
    
    @task(2)
    def like_post(self):
        """게시글 좋아요"""
        post_id = random.randint(1, 1000)
        self.client.post(f"/posts/{post_id}/like")
    
    @task(3)
    def view_comments(self):
        """댓글 조회"""
        post_id = random.randint(1, 1000)
        self.client.get(f"/posts/{post_id}/comments")
    
    @task(1)
    def create_comment(self):
        """댓글 작성"""
        post_id = random.randint(1, 1000)
        self.client.post(f"/posts/{post_id}/comments", json={
            "content": "This is a test comment"
        })
    
    @task(1)
    def view_profile(self):
        """내 프로필 조회"""
        self.client.get("/users/me")


class WebSocketUser(HttpUser):
    """WebSocket 연결 테스트"""
    
    wait_time = between(5, 10)
    
    @task
    def connect_websocket(self):
        """WebSocket 연결 시뮬레이션 (HTTP 업그레이드)"""
        room_id = random.randint(1, 10)
        # WebSocket은 직접 테스트 어려우므로 HTTP 엔드포인트로 대체
        self.client.get(f"/chats/{room_id}/messages")


class HealthCheckUser(HttpUser):
    """모니터링 엔드포인트 테스트"""
    
    wait_time = between(10, 30)
    
    @task(1)
    def health_check(self):
        """Health Check"""
        self.client.get("/health")
    
    @task(1)
    def ready_check(self):
        """Readiness Check"""
        self.client.get("/ready")
    
    @task(1)
    def metrics(self):
        """Metrics 조회"""
        self.client.get("/metrics")
    
    @task(1)
    def info(self):
        """App Info"""
        self.client.get("/info")


# =============================================================================
# 실행 방법:
# 
# 1. Locust 설치
#    pip install locust
# 
# 2. 로컬 실행
#    locust -f tests/load_test.py --host=http://localhost:5000
# 
# 3. 웹 UI 접속
#    http://localhost:8089
# 
# 4. CLI로 바로 실행 (웹 UI 없이)
#    locust -f tests/load_test.py --host=http://localhost:5000 \
#           --users 100 --spawn-rate 10 --run-time 5m --headless
# 
# 5. 결과 저장
#    locust -f tests/load_test.py --host=http://localhost:5000 \
#           --users 500 --spawn-rate 50 --run-time 10m --headless \
#           --html report.html --csv report
# =============================================================================
