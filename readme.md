python -m venv test -> test 가상환경 생성
source 가상환경이름/Scripts/activate -> 가상환경 실행
pip install -r requirments.txt -> 패키지 설치

가상환경 실행후 백엔드 디렉토리로 이동후

python manage.py migrate -> 변경사항 적용
python manage.py runserver -> 서버 실행

deactivate -> 가상환경 종료
