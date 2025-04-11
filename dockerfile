FROM python:3.11-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 애플리케이션 파일 복사
COPY . .

# 볼륨 설정 (ChromaDB 데이터를 유지하기 위함)
VOLUME /app/chroma_db

# 포트 설정
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "main.py"]