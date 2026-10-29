import os
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_code_review.db"
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-123456"
os.environ["AI_PROVIDER"] = "disabled"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-webhook-secret"
