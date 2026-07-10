"""전역 상수 정의."""

# ===== 세션 TTL (인메모리 세션 자동 만료) =====
SESSION_TTL_SECONDS = 300            # 마지막 활동 후 5분 경과 시 만료
SESSION_SWEEP_INTERVAL_SECONDS = 60  # 스위퍼 순회 주기 (1분)
