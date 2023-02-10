from sqlalchemy import text, Table, Column, Integer, String, ForeignKey, select, literal_column, and_, func, desc

# .env
# DB_CONNECTION=sqlite
# DB_NAME=memory
from sqlalchemy.orm import aliased

from create_database_tutorial import *

if __name__ == '__main__':
    create_database()
    session = Session()

    ## 스칼라 서브 쿼리, 상호연관 쿼리
    # 참고: https://rinuas.tistory.com/entry/%EC%84%9C%EB%B8%8C%EC%BF%BC%EB%A6%ACSub-Query
    # "서브쿼리"란 하나의 SQL문에 속한 SELECT문을 말하고 서브 쿼리의 바깥 쪽에 있는 SQL문을 "메인 쿼리"라고 합니다.
    # 이때 서브쿼리의 종류는 메인 쿼리 컬럼을 참조 여부, 서브쿼리의 선언 위치, 서브 쿼리 실행 결과 ROW수에 따라 종류가 나눠집니다
    #
    # 두 개의 테이블에서 데이터를 참조하여 SQL문을 작성하고 싶을 때, 사용한다.
    # JOIN도 마찬가지로 두 개 이상의 테이블에서 데이터를 가져오는데 사용하지만
    # => 보통은 2개의 테이블에서 1개의 결과를 얻고자 할때는 서브쿼리문을 사용하고,
    # => 3개 이상의 테이블에서 데이터를 얻고자 하는 경우는 JOIN을 이용하길 권장한다
    #    JOIN으로 작성된 SQL문은 서브쿼리가 포함된 SQL 문으로 변경할 수 있다
    # => 문법: (  ) 반드시 괄호 안에 쿼리문을 기재해야 한다. + 서브쿼리문은 반드시 연산자 오른쪽에 위치해야 한다.

    ## 종류
    # (1) 메인 쿼리 컬럼 참조 여부에 따른 구분
    #   1) 비상호 연관 서브 쿼리: 서브쿼리가 메인 쿼리의 컬럼을 참조하지 않고 독립적으로 수행하고 메인쿼리에 정보를 전달할 목적으로 사용 -> where절 서브쿼리 or updateSET이나insertValues에 들어갈 값1개용 서브쿼리
    #      ex> (update-where에 넣을 값 or 다중행 / update-SET에 넣을값 / insert-values (, , )중  들어갈 값 중 1개값)
    #   2) 상호 연관 서브쿼리 : 서브쿼리가 메인 쿼리 컬럼을 참조 -> select절 서브쿼리(스칼라 서브쿼리) or from절 서브쿼리(인라인 뷰)
    # (2) 서브쿼리 선언 위치에 따른 구분
    #   1) 스칼라 서브 쿼리 : SELECT 문의 컬럼 자리에 오는 서브 쿼리(상호 연관 서브쿼리- 바깥 main 속 칼럼을 참조하여 select subquery 작성)
    #   2) 인라인 뷰 : FROM절 자리에 오는 서브 쿼리 (상호 연관 서브 쿼리 - 바깥 main 속 칼럼을 참조하여 select subquery 작성)
    #   3) 중첩 서브 쿼리 : Where절 자리에 오는 서브 쿼리 (비상호 연관 서브 쿼리 - 바깥 main 속 칼럼을 참조하지 않고 타table?에서 단독으로 subquery로 값을 구성하여 연산자의 값을 마련한다.)
    # (3) 서브 쿼리 실행 결과 ROW수에 따른 구분
    #   1) 단일행 서브쿼리(서브 쿼리 연산결과 ROW1개)  = > <
    #   2) 단중행 서브쿼리(서브 쿼리 연산결과 ROW2개이상):IN, ANY, ALL, EXISTS
    #     -> EXISTS는 상호연관서브쿼리(바깥main쿼리 참조하는 상호연관 서브쿼리에서만 사용?!)    # (1) 메인 쿼리 컬럼 참조 여부에 따른 구분


    ## 예시
    # (1) 메인 쿼리 컬럼 참조 여부에 따른 구분
    #   1) 비상호 연관 서브 쿼리: 서브쿼리가 메인 쿼리의 컬럼을 참조하지 않고 독립적으로 수행하고 메인쿼리에 정보를 전달할 목적으로 사용됩니다.
    #     -> 메인칼럼없이, 독립적수행 / 메인쿼리에 정보전달 ex> where절의 중첩서브쿼리 / sub부터수행후 main실행됨.
    #     -> 서브쿼리가 1개값 단일행 서브쿼리 -> 단일행 연산자 =
    #       ex1> 비상호연관(where) = 중첩 서브쿼리 & 단일행(연산자)
    #       -> 최고급여를 받는(max값 1개 -> main where로) 사원정보
    #           select employee_id, salary
    #           from employees
    #           where salary = (select max(salary)
    #                           from employees);
    #       ex2> 비상호연관(where) = 중첩 서브쿼리 & 1칼럼(값) 다중행(연산자 IN)
    #       -> 부서번호 30번에 소속된 직급(pk조회아니므로 다중행)과 동일한 직급을(다중행의 equal연산자 IN) 가진 사원을 조회(사번, 직급, 부서번호출력)
    #            select employee_id, job_id, department_id
    #            from employees
    #            where job_id IN (select distinct job_id
    #                              from employees
    #                              where department_id = 30);
    #       ex3> 비상호연관(where) = 중첩 서브쿼리 & 1칼럼(값) 다중행(연산자 ALL for 다중행의 최대값보다 큰 )
    #       -> 부서번호가 30번인 사원들(pk조회아니므로 다중행)의 급여(다중value)보다 많이(전체 and > ) 받는( > ALL) 사원정보를 조회
    #       => 다중행에 대한 대소는 > ALL ( )  or   > ANY ( ) 로 쓴다.
    #       => 서브쿼리 결과기 2ROW 이상이므로 다중행 서브쿼리의 비교를 위해서는 IN(=), (>= or<=) ALL, ANY, EXISTS 연산자를 사용해야 한다고 개요에서 설명했었다.
    #       => 다중행 보다 큰 -> 다중행의 max값보다 큰 -> > ALL ()
    #            select employee_id, salary
    #            from employees
    #            where salary > ALL (select salary
    #                                 from employees
    #                                 where department_id = 30);
    #      =>  > ALL ()은 ()안의 max값보다 큰 값을 찾는 것이니 subquery에 max집계를 해서 해결할 수 도 있다.
    #            select employee_id, salary
    #            from employees
    #            where salary > (select max(salary)
    #                            from employees
    #                            where department_id = 30
    #                            group by department_id);

    #       ex4> 비상호연관(where) = 중첩 서브쿼리 & 1칼럼(값) 다중행(연산자 ANY for 다중행의 최소값 큰 )
    #       -> 부서번호가 30번인 사원들(pk조회아니므로 다중행)의 최소 급여보다 많이 받는 사원정보를 조회
    #       => 다중행의 최소보다 큰 -> 다중행의 min값보다 큰 -> > ANY ()
    #            select employee_id, salary
    #            from employees
    #            where salary > ANY (select salary
    #                                from employees
    #                                where department_id = 30);
    #        =>
    #            select employee_id, salary
    #            from employees
    #            where salary > (select min(salary)
    #                            from employees
    #                            where department_id = 30
    #                            group by department_id);

    #       ex5> 비상호연관(where) = 중첩 서브쿼리 & 다중 칼럼 다중행(연산자 IN for 해당값에 해당하는 것들)
    #       -> 부서별 최고급여를 받는 사원 정보 (사번, 입사일자, 부서번호 , 급여), 부서번호로 오름차순정렬
    #       => where절에 subquery결과가 다중컬럼이면 -> where의 인자에 다중칼럼으로 조건을 줄 수 있다.
    #          where and
    #            select employee_id, hire_date, department_id, salary
    #            from employees
    #            where (department_id, salary) in (select department_id, max(salary)
    #                                              from employees
    #                                              group by department_id)
    #            order by department_id asc;

    #       => 단일행이었으면 칼럼별로 and를 줘서 where col1==a and col2==b 이지만,
    #       => 다중행이면,   칼럼튜플로 만들고    where (co1, col2) IN (a,b)칼럼의 다중행
    #       => SQLALCHEMY에선    session.query(Ent).filter(     tuple_(Ent.name, Ent.type)  .in_(  items  ))
    #          https://stackoverflow.com/questions/50245422/how-to-filter-where-in-multiple-columns-simultaneously-in-sqlalchemy-orm


    ## 다중행 subquery 예시-> select 뿐만 아니라,insert/update 확인해보기
    ## update
    #       ex6> 비상호연관(select-where에 넣을 값 or 다중행/ update-SET에 넣을값) = 중첩 서브쿼리 & 1칼럼(값) 단일행(pk인 id로 검색)
    #       ->  사번이 178인 사원의 부서번호를(main update set) 사번이 103번이 소속된 부서번호로(subquery로 값 찾기) 변경하시오.
    #           update employees
    #           set department_id = (select department_id
    #                                 from employees
    #                                 where employee_id = 103)
    #           where employee_id = 178;

    ## insert
    #       ex6> 비상호연관(update-where에 넣을 값 or 다중행 / update-SET에 넣을값 / insert-values (, , )중  들어갈 값 중 1개값) = 중첩 서브쿼리 & 1칼럼(값) 단일행(pk인 id로 검색)
    #       ->  부서번호를 등록하시오. 단, 부서번호 : 280, 부서명 : Research and Developmenst, location_id = seattle에 위치
    #           insert into departments (department_id, department_name, location_id)
    #           values (280, 'Research and Development',
    #                                                  (select location_id
    #                                                   from locations
    #                                                   where lower(city) = 'seattle'));

    # (2) 서브쿼리 선언 위치에 따른 구분
    #   1) 스칼라 서브 쿼리 : SELECT 문의 컬럼 자리에 오는 서브 쿼리(상호 연관 서브쿼리- 바깥 main 속 칼럼을 참조하여 select subquery 작성)
    #   2) 인라인 뷰 : FROM절 자리에 오는 서브 쿼리 (상호 연관 서브 쿼리 - 바깥 main 속 칼럼을 참조하여 select subquery 작성)
    #   3) 중첩 서브 쿼리 : Where절 자리에 오는 서브 쿼리 (비상호 연관 서브 쿼리 - 바깥 main 속 칼럼을 참조하지 않고 타table?에서 단독으로 subquery로 값을 구성하여 연산자의 값을 마련한다.)
    # (3) 서브 쿼리 실행 결과 ROW수에 따른 구분
    #   1) 단일행 서브쿼리(서브 쿼리 연산결과 ROW1개)
    #   2) 단중행 서브쿼리(서브 쿼리 연산결과 ROW2개이상):IN, ANY, ALL, EXISTS
    #     -> EXISTS는 상호연관서브쿼리(바깥main쿼리 참조하는 상호연관 서브쿼리에서만 사용?!)






    #   2) 상호 연관 서브쿼리 : 서브쿼리가 메인 쿼리 컬럼을 참조. (1) select절서브쿼리 - 스칼라 서브쿼리 (2) from절 서브쿼리 - 인라인 뷰
    ## => 메인쿼리가 먼저 수행되고, 서브쿼리가 수행된다.
    ## => 테이블 별칭이 필수이다.
    ## => 인라인뷰, 스칼라 서브쿼리가 상호연관 서브쿼리에서 사용한다.
    ## => 조회대상 테이블이 2개 정도인 경우는 스칼라 서브쿼리를 사용할 것을 권장하고,
    #     3개 이상인 경우는 조인을 사용할 것을 권장한다.

    #       ex7> 상호연관(= 중첩 서브쿼리(X) 스칼라 ) & 2칼럼, 다중행??
    #       ->  사번이 100번인 사원의 정보 사번, 부서번호, 부서명(타entity가 select에) 를 조회

    ##      => 테이블2개일 땐, select -> from 여러테이블을 두고 where로 인해 join으로 풀기
    #           select emp.employee_id, dept.department_id, dept.department_name
    #           from employees emp, departments dept
    #           where emp.department_id = dept.department_id
    #                 and emp.employee_id = 100;

    ##      => 스칼라 서브쿼리로 풀기
    ##         타Entity를 select에 올리되, join on 없이, where절에 main쿼리에서 where로 뽑힌 main select상의 칼럼을 이용한다
    #       ->  사번이 100번인 사원의 정보 사번, 부서번호, 부서명(타entity의 정보를, main select에 완성된 fk정보를 이용해서 뽑아낸다.) 를 조회
    #          -> 스칼라 서브쿼리는 select문의 메인컬럼 자리에 위치하며,  메인쿼리의 컬럼을 이용하여 결과를 출력하는 것을 볼수있다.
    #          -> 그래서 스칼라 서브쿼리를 메인쿼리의 컬럼을 참조한다고 해서, 상호 연관 서브쿼리라고 하는것이다.
    #          -> 퀴리문 실행 순서는 실행순서 from > where > select > 서브쿼리 이다.

    #    select emp.employee_id,
    #           emp.department_id,
    #           (select department_name
    #            from departments dept
    #            where dept.department_id = emp.department_id) as "부서명"
    #     from employees emp
    #     where emp.employee_id = 100;

    ## where절 subquery 중 EXISTS만 상호연관 서브쿼리이다.(from -> where exists (    where A.col1 == B.col2)
    #       ex8> 상호연관(= 중첩 서브쿼리)
    #       ->  emp가 1개라도 존재하는 depart의 id와 name
    #         select dept.department_id, dept.department_name
    #         from departments dept
    #         where exists (select 1
    #                       from employees emp
    #                       where emp.department_id = dept.department_id);
    # EXIST 연산자는 데이터가 존재여부를 체크하는 연산자이다. 단1개의 row라도 존재한다면 where 조건을 만족하게 된다.        뒤에오는 서브커리의 컬럼자리에 1을 기재하였는데, 무엇이 오든 관계없다.  employee_id, 등 뭐든 관계없다.        단지 해당 row가 존재하는지 여부만 체크하기 때문이다.
    # 반대로 row가 존재하지 않는경우는 where 뒤애 not exists 를 기재하면 된다.