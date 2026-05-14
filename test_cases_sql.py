# test_cases_sql.py
from dataclasses import dataclass
from typing import List


@dataclass
class Case:
    id: str
    question: str
    gold_sql: str
    notes: str = ""


TEST_CASES: List[Case] = [
    Case(
        id="avg_salary_engineering",
        question="What is the average salary in Engineering?",
        gold_sql="SELECT AVG(salary) FROM employees WHERE dept='Engineering';",
    ),
    Case(
        id="highest_salary",
        question="Who earns the highest salary?",
        gold_sql="SELECT name, salary FROM employees ORDER BY salary DESC LIMIT 1;",
    ),
    Case(
        id="salary_gt_25000_desc",
        question="List employees with salary > 25000 ordered by salary descending.",
        gold_sql="SELECT name, salary FROM employees WHERE salary > 25000 ORDER BY salary DESC;",
    ),
    Case(
        id="count_by_dept",
        question="How many employees are in each department?",
        gold_sql="SELECT dept, COUNT(*) FROM employees GROUP BY dept ORDER BY dept;",
    ),
    Case(
        id="top2_engineering",
        question="Top 2 highest paid people in Engineering (name + salary).",
        gold_sql=(
            "SELECT name, salary FROM employees "
            "WHERE dept='Engineering' ORDER BY salary DESC LIMIT 2;"
        ),
    ),
    Case(
        id="min_salary",
        question="Who has the lowest salary?",
        gold_sql="SELECT name, salary FROM employees ORDER BY salary ASC LIMIT 1;",
    ),
    Case(
        id="dept_avg_salary_desc",
        question="Show average salary per department, from highest to lowest.",
        gold_sql=(
            "SELECT dept, AVG(salary) AS avg_salary "
            "FROM employees GROUP BY dept ORDER BY avg_salary DESC;"
        ),
    ),
    Case(
        id="marketing_titles",
        question="List all job titles in Marketing.",
        gold_sql="SELECT title FROM employees WHERE dept='Marketing' ORDER BY title;",
    ),
    Case(
        id="people_named_ends_with_son",
        question="List employees whose name ends with 'son'.",
        gold_sql="SELECT name FROM employees WHERE name LIKE '%son' ORDER BY name;",
    ),
    Case(
        id="no_result_edge",
        question="List employees with salary > 100000.",
        gold_sql="SELECT name, salary FROM employees WHERE salary > 100000;",
        notes="edge: empty result",
    ),
    
    # ---------- Hard ----------

    Case(
        id="not_engineering",
        question="List employees who do not work in Engineering.",
        gold_sql="""
        SELECT name
        FROM employees
        WHERE dept != 'Engineering'
        ORDER BY name;
        """,
    ),

    Case(
        id="engineering_or_high_salary",
        question="List employees who work in Engineering or earn more than 35000.",
        gold_sql="""
        SELECT name
        FROM employees
        WHERE dept='Engineering'
        OR salary > 35000
        ORDER BY name;
        """,
    ),

    Case(
        id="dept_above_company_avg",
        question="Which departments have an average salary higher than the company average?",
        gold_sql="""
        SELECT dept
        FROM employees
        GROUP BY dept
        HAVING AVG(salary) >
        (
            SELECT AVG(salary)
            FROM employees
        );
        """,
    ),

    Case(
        id="highest_paid_per_dept",
        question="List the highest paid employee in each department.",
        gold_sql="""
        SELECT name, dept, salary
        FROM employees e
        WHERE salary =
        (
            SELECT MAX(salary)
            FROM employees
            WHERE dept = e.dept
        )
        ORDER BY dept;
        """,
    ),

    Case(
        id="dept_more_than_two",
        question="Which departments have more than two employees?",
        gold_sql="""
        SELECT dept
        FROM employees
        GROUP BY dept
        HAVING COUNT(*) > 2
        ORDER BY dept;
        """,
    ),
]