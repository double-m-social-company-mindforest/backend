import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """로깅 설정"""
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # 로그 레벨 설정
    log_level = logging.DEBUG if debug else logging.INFO
    
    # 로그 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 루트 로거 설정
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # 콘솔 출력
        ]
    )
    
    # 프로덕션 환경에서는 파일 로그도 추가
    if not debug:
        # logs 디렉토리 생성
        os.makedirs("logs", exist_ok=True)
        
        # 파일 핸들러 추가 (로테이션)
        file_handler = RotatingFileHandler(
            "logs/app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
    
    # SQLAlchemy 로그 레벨 조정
    if not debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Debug: {debug}")