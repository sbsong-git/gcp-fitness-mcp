# 필요한 라이브러리 설치:
# pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import json
import sys

# Google Fitness API 관련 상수
SCOPES = ['https://www.googleapis.com/auth/fitness.activity.read',
          'https://www.googleapis.com/auth/fitness.heart_rate.read',
          'https://www.googleapis.com/auth/fitness.body.read']

# 인증 정보를 저장할 파일
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json' 
# 인증 에러 발생 시 파일 위치를 절대경로로 지정 (D:\MCP_App\credentials.json)

# MCP 서버 생성
mcp = FastMCP("google-fitness", 
              title="Google Fitness MCP 서버",
              version="1.0.0",
              description="Google Fitness API 데이터에 접근하기 위한 MCP 서버")

# Google API 클라이언트 인증 함수
def get_google_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_info(
            json.load(open(TOKEN_FILE)), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("브라우저에서 Google 계정 인증 중...", file=sys.stderr)
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            print("인증 완료!", file=sys.stderr)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds

@mcp.tool()
def get_steps_data(days: int = 7) -> dict:
    """
    Google Fitness API에서 걸음 수 데이터를 가져옵니다.
    
    Args:
        days: 가져올 데이터의 일수 (기본값: 7일)
        
    Returns:
        걸음 수 데이터를 포함한 딕셔너리
    """
    try:
        # 날짜 범위 계산
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Google 인증
        creds = get_google_credentials()
        
        # Fitness API 서비스 생성
        fitness_service = build('fitness', 'v1', credentials=creds)
        
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 하루 단위로 데이터 집계
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        
        response = fitness_service.users().dataset().aggregate(userId="me", body=body).execute()
        
        return {
            "success": True,
            "data": response,
            "message": f"{days}일간의 걸음 수 데이터를 성공적으로 가져왔습니다."
        }
            
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

@mcp.tool()
def get_heart_rate_data(days: int = 7) -> dict:
    """
    Google Fitness API에서 심박수 데이터를 가져옵니다.
    
    Args:
        days: 가져올 데이터의 일수 (기본값: 7일)
        
    Returns:
        심박수 데이터를 포함한 딕셔너리
    """
    try:
        # 날짜 범위 계산
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        # Google 인증
        creds = get_google_credentials()
        
        # Fitness API 서비스 생성
        fitness_service = build('fitness', 'v1', credentials=creds)
        
        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            }],
            "bucketByTime": {"durationMillis": 3600000},  # 1시간 단위로 데이터 집계
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        
        response = fitness_service.users().dataset().aggregate(userId="me", body=body).execute()
        
        return {
            "success": True,
            "data": response,
            "message": f"{days}일간의 심박수 데이터를 성공적으로 가져왔습니다."
        }
            
    except Exception as e:
        print(f"오류 발생: {str(e)}", file=sys.stderr)
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

# 메인 실행부
if __name__ == "__main__":
    # 서버가 시작되었음을 로그로 남기기
    print("Google Fitness MCP 서버를 시작합니다...", file=sys.stderr)
    
    # 최신 MCP SDK 방식으로 서버 실행
    mcp.run()