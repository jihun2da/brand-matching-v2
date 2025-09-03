#!/usr/bin/env python3
"""
Brand Matching System V2 배포 도구

이 스크립트는 다양한 플랫폼에 애플리케이션을 배포하는 데 도움을 줍니다.
"""

import os
import subprocess
import sys
import argparse

def run_command(command, description):
    """명령어를 실행하고 결과를 출력합니다."""
    print(f"\n🔄 {description}")
    print(f"실행 중: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ 성공: {description}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {description}")
        print(f"오류: {e.stderr}")
        return False

def check_requirements():
    """필요한 도구들이 설치되어 있는지 확인합니다."""
    print("📋 필수 도구 확인 중...")
    
    tools = {
        'git': 'git --version',
        'python': 'python --version',
        'pip': 'pip --version'
    }
    
    missing_tools = []
    for tool, command in tools.items():
        try:
            subprocess.run(command, shell=True, check=True, capture_output=True)
            print(f"✅ {tool} 설치됨")
        except subprocess.CalledProcessError:
            print(f"❌ {tool} 설치 필요")
            missing_tools.append(tool)
    
    return len(missing_tools) == 0

def deploy_heroku(app_name):
    """Heroku에 배포합니다."""
    print("\n🚀 Heroku 배포 시작")
    
    commands = [
        ("heroku login", "Heroku 로그인"),
        (f"heroku create {app_name}", f"Heroku 앱 생성: {app_name}"),
        ("heroku config:set FLASK_ENV=production", "환경 변수 설정"),
        ("git add .", "파일 스테이징"),
        ("git commit -m 'Deploy to Heroku'", "커밋 생성"),
        ("git push heroku main", "Heroku에 배포")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    print(f"\n🎉 Heroku 배포 완료! https://{app_name}.herokuapp.com 에서 확인하세요.")
    return True

def deploy_vercel():
    """Vercel에 배포합니다."""
    print("\n🚀 Vercel 배포 시작")
    
    # Vercel CLI 설치 확인
    try:
        subprocess.run("vercel --version", shell=True, check=True, capture_output=True)
        print("✅ Vercel CLI 설치됨")
    except subprocess.CalledProcessError:
        print("📦 Vercel CLI 설치 중...")
        if not run_command("npm install -g vercel", "Vercel CLI 설치"):
            return False
    
    commands = [
        ("vercel login", "Vercel 로그인"),
        ("vercel --prod", "Vercel에 배포")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    print("\n🎉 Vercel 배포 완료!")
    return True

def setup_local():
    """로컬 개발 환경을 설정합니다."""
    print("\n🔧 로컬 환경 설정 시작")
    
    commands = [
        ("python -m venv venv", "가상환경 생성"),
        ("pip install -r requirements.txt", "패키지 설치")
    ]
    
    # Windows vs Unix 가상환경 활성화
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate && "
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate && "
    
    commands[1] = (activate_cmd + commands[1][0], commands[1][1])
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    print("\n🎉 로컬 환경 설정 완료!")
    print("다음 명령어로 애플리케이션을 실행하세요:")
    if os.name == 'nt':
        print("venv\\Scripts\\activate && python app.py")
    else:
        print("source venv/bin/activate && python app.py")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Brand Matching System V2 배포 도구")
    parser.add_argument("command", choices=["local", "heroku", "vercel"], 
                       help="배포 대상을 선택하세요")
    parser.add_argument("--app-name", help="Heroku 앱 이름 (heroku 배포시 필요)")
    
    args = parser.parse_args()
    
    print("🎯 Brand Matching System V2 배포 도구")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ 필수 도구가 설치되지 않았습니다. 설치 후 다시 시도해주세요.")
        sys.exit(1)
    
    success = False
    
    if args.command == "local":
        success = setup_local()
    elif args.command == "heroku":
        if not args.app_name:
            print("❌ Heroku 배포시 --app-name 옵션이 필요합니다.")
            sys.exit(1)
        success = deploy_heroku(args.app_name)
    elif args.command == "vercel":
        success = deploy_vercel()
    
    if success:
        print("\n🎉 모든 작업이 완료되었습니다!")
    else:
        print("\n❌ 배포 중 오류가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main() 