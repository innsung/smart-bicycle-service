# `bike_member` 테이블 명세서

`bike_member`는 회원의 로그인 정보, 프로필, 권한, 약관 동의 및 계정 상태를 저장하는 테이블

## 컬럼 명세

| 컬럼명 | MySQL 타입 | NULL | Key | 의미 | 예시 |
|---|---|---:|---|---|---|
| `member_id` | `INT` | 불가 | `PRI` | 회원을 구분하는 내부 고유번호. 회원가입 시 자동 증가. | `1` |
| `email` | `VARCHAR(255)` | 불가 | `UNI` | 로그인에 사용하는 이메일. 중복 가입을 방지하기 위해 고유값 설정. | `rider@example.com` |
| `password_hash` | `VARCHAR(255)` | 불가 |  | bcrypt로 단방향 암호화한 비밀번호. 실제 비밀번호는 저장 X. | `$2b$12$...` |
| `nickname` | `VARCHAR(50)` | 불가 | `UNI` | 화면과 커뮤니티에 표시할 회원 이름(닉네임). 다른 회원과 중복 X. | `따릉이왕` |
| `role` | `VARCHAR(20)` | 불가 |  | 회원 권한을 구분. | `USER`, `ADMIN` |
| `riding_styles` | `TEXT` | 허용 |  | 회원이 선택한 라이딩 스타일 목록을 JSON 문자열로 저장. 아무것도 선택하지 않아도 됨. | `["로드","도심 라이딩"]` |
| `marketing_consent` | `TINYINT(1)` | 불가 |  | 이벤트·혜택 등 마케팅 정보 수신 동의 여부. | `1`: 동의, `0`: 미동의 |
| `terms_accepted_at` | `DATETIME` | 불가 |  | 필수 이용약관과 개인정보처리방침에 동의한 시간. | `2026-08-13 10:30:00` |
| `is_active` | `TINYINT(1)` | 불가 |  | 현재 사용할 수 있는 계정인지 나타냄. 정지·탈퇴 처리에 사용. | `1`: 활성, `0`: 비활성 |
| `created_at` | `DATETIME` | 불가 |  | 회원 계정이 생성된 시간. | `2026-08-13 10:30:00` |
| `updated_at` | `DATETIME` | 불가 |  | 회원정보가 마지막으로 변경된 시간. | `2026-08-13 11:20:00` |

## 주요 컬럼 관계

```text
member_id
→ 시스템 내부에서 회원을 구분하는 기본키

email + password_hash
→ 로그인 인증에 사용

nickname + riding_styles
→ 회원 프로필에 사용

role + is_active
→ 권한과 계정 상태 관리에 사용

marketing_consent + terms_accepted_at
→ 약관 및 마케팅 동의 관리에 사용

created_at + updated_at
→ 계정 생성·수정 이력 관리에 사용
```

## 비밀번호 저장 방식

```text
사용자 입력
test-password-123

bcrypt 해시 후 DB 저장
$2b$12$...
```

## `riding_styles` 저장 방식

라이딩 스타일은 선택 입력이며 여러 값을 JSON 문자열로 저장.

```json
["로드", "MTB", "도심 라이딩"]
```

선택하지 않은 경우 빈 배열 `[]`을 저장. 컬럼 자체는 `NULL`도 허용.

## `marketing_consent` 값

MySQL의 `TINYINT(1)`은 Boolean 값으로 사용합니다.

| 프론트 체크박스 | API 값 | DB 값 | 의미 |
|---|---|---:|---|
| 체크 해제 | `false` | `0` | 마케팅 수신 미동의 |
| 체크 | `true` | `1` | 마케팅 수신 동의 |

