[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# Match Gathering Server

모델 개발 목적으로 롤 패치마다 특정 조건을 만족하는 경기를 수집하는 서버입니다.

천상계(챌린저, 그랜드마스터) 구간에서는 정답에 가까운 행동을 한다고 가정하고, 비정상적인 경기를 제외한 모든 경기 목록을 수집합니다.
하위 구간은 실력에 맞는 플레이를 한다고 보고, 실력별로 모델의 유효성을 검증하기 위한 목적으로 특정 개수(현재는 400개)씩 목록을 수집합니다.

## How to Setup
서버 프레임워크로 FastAPI를 사용하므로, FastAPI 및 관련 모듈을 설치해야 합니다.
```
pip install "fastapi[all]"
```
만약 설치에 실패할 경우, 모듈마다 따로따로 설치하면 오류가 발생하지 않을 수 있습니다.
```
pip install fastapi
pip install "uvicorn[standard]"
```
Uvicorn은 ASGI web server로 FastAPI로 만든 서버를 실행하기 위해 필요한 모듈입니다.

## How to Run
```
uvicorn app.main:app --reload --port 8000
```
서버를 실행하려면 위의 명령어를 실행하면 됩다. 정상작동할 경우 'INFO:     Uvicorn running on'라는 로그가 남습니다.
--reload 옵션을 파일을 수정할 때마다 서버를 재실행하는 옵션이고, --port 옵션은 서버를 실행할 포트 번호입니다.
두 옵션은 목적에 따라 생략할 수 있습니다. (기본 port는 8000)

## How to Test
```
$ python -m unittest
```
## Authors
임창준 - changjun.lim@ggq.gg


---
Copyright 2022 GGQ Company Inc. All rights reserved.  
Unauthorized copying of this file, via any medium, is strictly prohibited.  
Proprietary and confidential.

See the CONFIDENTIAL file for more info.
