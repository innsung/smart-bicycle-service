# 데이터베이스 확인
show databases;

# fastapi_db 데이터베이스 생성
create database fastapi_db
	character set utf8mb4
    collate utf8mb4_unicode_ci;

# database 사용
use fastapi_db;

# 선택
select database();

# 테이블 리스트 조회
show tables;

-- desc books;
-- desc python_books;
-- drop table member; 
-- desc member;
desc bike_member;

-- select * from todos;
-- select * from books;
-- select * from python_books;
-- select * from member;
select * from bike_member;

