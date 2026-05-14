# benchmark_sql_agent.py
import time
import json
import sqlite3
import itertools
import statistics
import random
import string
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter


# import from your file
from llm_sql_agent import init_db, build_agent, DB_PATH

# import cases from separate file
from test_cases_sql import TEST_CASES, Case

from langchain_community.callbacks import get_openai_callback

def run_sql_raw_with_cols(db_path: str, sql: str) -> Tuple[List[Tuple], List[str]]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in (cur.description or [])]
    conn.close()
    return rows, cols


def normalize_value(x, float_ndigits=6):
    if isinstance(x, str):
        return x.strip()
    if isinstance(x, float):
        return round(x, float_ndigits)
    return x


def normalize_rows(rows: List[Tuple], float_ndigits=6) -> List[Tuple]:
    return [tuple(normalize_value(v, float_ndigits) for v in r) for r in rows]


def rows_equal(a: List[Tuple], b: List[Tuple], ignore_order=True) -> bool:
    if ignore_order:
        return Counter(a) == Counter(b)
    return a == b


def project_rows(rows: List[Tuple], idxs: List[int]) -> List[Tuple]:
    return [tuple(r[i] for i in idxs) for r in rows]


def best_match_executed_sql(
    db_path: str,
    sql_logs: List[str],
    gold_sql: str,
    ignore_order: bool = True,
    float_ndigits: int = 6,
) -> Tuple[Optional[str], Optional[List[Tuple]], bool, Optional[str]]:
    # run gold once
    try:
        gold_rows_raw, gold_cols = run_sql_raw_with_cols(db_path, gold_sql)
        gold_rows = normalize_rows(gold_rows_raw, float_ndigits)
    except Exception as e:
        return None, None, False, f"Gold SQL failed: {e}"

    k = len(gold_cols) if gold_cols else (len(gold_rows[0]) if gold_rows else 0)

    candidates = []
    for s in sql_logs:
        if not isinstance(s, str) or "select" not in s.lower():
            continue
        try:
            agent_rows_raw, agent_cols = run_sql_raw_with_cols(db_path, s)
            agent_rows_raw = agent_rows_raw or []
            agent_cols = agent_cols or []
        except Exception:
            continue

        # normalize full rows first
        agent_rows_norm_full = normalize_rows(agent_rows_raw, float_ndigits)

        # case: both empty
        if not gold_rows and not agent_rows_norm_full:
            return s, agent_rows_norm_full, True, None

        # if we know column names, try name-based projection first
        projections = []

        if gold_cols and agent_cols:
            if all(c in agent_cols for c in gold_cols):
                idxs = [agent_cols.index(c) for c in gold_cols]
                projections.append(idxs)

        # fallback: brute force choose any k columns
        if k > 0 and agent_rows_raw and len(agent_rows_raw[0]) >= k:
            m = len(agent_rows_raw[0])
            for idxs in itertools.combinations(range(m), k):
                projections.append(list(idxs))

        # remove duplicates
        uniq = []
        seen = set()
        for idxs in projections:
            t = tuple(idxs)
            if t not in seen:
                seen.add(t)
                uniq.append(idxs)

        for idxs in uniq:
            proj = project_rows(agent_rows_norm_full, idxs)
            if rows_equal(proj, gold_rows, ignore_order=ignore_order):
                return s, proj, True, None

        candidates.append((s, agent_rows_norm_full, agent_cols))

    # no exact match
    return None, None, False, None

def result_completeness(agent_rows: List[Tuple], gold_rows: List[Tuple]) -> float:
    if not gold_rows:
        return 1.0 if not agent_rows else 0.0

    gold_set = Counter(gold_rows)
    agent_set = Counter(agent_rows or [])

    matched = 0
    for row in gold_set:
        matched += min(gold_set[row], agent_set.get(row, 0))

    return matched / len(gold_rows)

def add_noise(question: str) -> str:

    noise_type = random.choice([
        "delete_char",
        "swap_char",
        "replace_char",
        "keyboard_typo",
        "double_typo",
        "reorder_phrase"
    ])

    # ---------- character level ----------
    chars = list(question)

    if noise_type == "delete_char" and len(chars) > 4:
        idx = random.randint(0, len(chars)-1)
        del chars[idx]
        return "".join(chars)

    if noise_type == "swap_char" and len(chars) > 4:
        idx = random.randint(0, len(chars)-2)
        chars[idx], chars[idx+1] = chars[idx+1], chars[idx]
        return "".join(chars)

    if noise_type == "replace_char":
        idx = random.randint(0, len(chars)-1)
        chars[idx] = random.choice(string.ascii_lowercase)
        return "".join(chars)

    # ---------- keyboard typo ----------
    if noise_type == "keyboard_typo":

        keyboard_neighbors = {
            "a":"sqwz","b":"vghn","c":"xdfv","d":"erfcxs",
            "e":"rdsw","f":"rtgvcd","g":"tyhbvf","h":"yujnbg",
            "i":"okju","j":"uikmnh","k":"iolmj","l":"opk",
            "m":"njk","n":"bhjm","o":"pikl","p":"ol",
            "q":"wa","r":"tfde","s":"wedxza","t":"ygfr",
            "u":"yihj","v":"cfgb","w":"qase","x":"zsdc",
            "y":"uhtg","z":"asx"
        }

        idx = random.randint(0, len(chars)-1)
        ch = chars[idx].lower()

        if ch in keyboard_neighbors:
            chars[idx] = random.choice(keyboard_neighbors[ch])

        return "".join(chars)

    # ---------- double typo (swap inside word) ----------
    if noise_type == "double_typo":

        words = question.split()

        if not words:
            return question

        w_idx = random.randint(0, len(words)-1)
        word = list(words[w_idx])

        if len(word) > 4:
            i = random.randint(1, len(word)-3)
            word[i], word[i+1] = word[i+1], word[i]
            words[w_idx] = "".join(word)

        return " ".join(words)

    # ---------- reorder phrase ----------
    if noise_type == "reorder_phrase":

        words = question.split()

        if len(words) < 5:
            return question

        i = random.randint(0, len(words)-3)
        j = random.randint(i+1, len(words)-1)

        segment = words[i:j]
        random.shuffle(segment)

        words[i:j] = segment

        return " ".join(words)

    return question

def main():
    init_db()
    agent = build_agent(verbose=False)

    # -------- Patch db.run to log SQL queries ----------
    sql_logs: List[str] = []

    db_obj = None
    for tool in getattr(agent, "tools", []) or []:
        if hasattr(tool, "db"):
            db_obj = tool.db
            break

    if db_obj is None:
        raise RuntimeError(
            "Could not locate SQLDatabase from agent.tools. "
            "Try agent.get_tools() or inspect agent structure."
        )

    original_run = db_obj.run

    def logged_run(command: str, *args, **kwargs):
        sql_logs.append(command)
        return original_run(command, *args, **kwargs)

    db_obj.run = logged_run  # monkey patch

    # -------- Benchmark cases (imported) ----------
    cases: List[Case] = TEST_CASES

    results: List[Dict[str, Any]] = []
    total_pass = 0
    # ---- successful query counts and latency ----
    successful_query_counts = []
    successful_latency = []

    robust_results: List[Dict[str, Any]] = []

    original_correct = 0
    robust_correct = 0

    for c in cases:
        sql_logs.clear()

        # --- Run agent ---
        t0 = time.perf_counter()

        with get_openai_callback() as cb:
            out = agent.invoke({"input": c.question})

        t1 = time.perf_counter()

        token_used = cb.total_tokens
        prompt_tokens = cb.prompt_tokens
        completion_tokens = cb.completion_tokens

        # --- Semantic SQL matching ---
        executed_sql, agent_rows, passed, match_err = best_match_executed_sql(
            DB_PATH,
            sql_logs,
            c.gold_sql,
            ignore_order=True,
            float_ndigits=6,
        )

        # --- Gold rows (only for display / logging) ---
        gold_rows_raw, _ = run_sql_raw_with_cols(DB_PATH, c.gold_sql)
        gold_rows = normalize_rows(gold_rows_raw)

        # NEW: fallback to last SQL result if no exact match
        if agent_rows is None and sql_logs:
            last_sql = sql_logs[-1]

            try:
                rows_raw, _ = run_sql_raw_with_cols(DB_PATH, last_sql)
                agent_rows = normalize_rows(rows_raw)
            except Exception:
                agent_rows = []
                
        # --- Error handling ---
        error = match_err
        if executed_sql is None and error is None:
            error = "No matching SELECT found in agent SQL logs."

        total_pass += int(passed)
        if passed:
            original_correct += 1
            successful_query_counts.append(len(sql_logs))
            successful_latency.append(t1 - t0)
            
        completeness = result_completeness(agent_rows or [], gold_rows)

        results.append(
            {
                "id": c.id,
                "question": c.question,
                "gold_sql": c.gold_sql,
                "gold_rows": gold_rows,
                "executed_sql": executed_sql,
                "agent_rows": agent_rows,
                "passed": passed,
                "completeness": round(completeness, 4),
                "latency_sec": round(t1 - t0, 4),
                "sql_query_count": len(sql_logs),
                "token_usage": token_used,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "sql_logs": sql_logs.copy(),
                "agent_output": out.get("output", out),
                "notes": c.notes,
                "error": error,
            }
        )

        # ---- Robustness test ----
        noisy_question = add_noise(c.question)
        print("ROBUST TEST:", noisy_question)
        sql_logs.clear()

        try:
            noisy_out = agent.invoke({"input": noisy_question})

            executed_sql_n, agent_rows_n, passed_n, match_err_n = best_match_executed_sql(
                DB_PATH,
                sql_logs,
                c.gold_sql,
                ignore_order=True,
                float_ndigits=6,
            )

            if passed and passed_n:
                robust_correct += 1

            robust_results.append(
                {
                    "id": c.id,
                    "original_question": c.question,
                    "noisy_question": noisy_question,
                    "executed_sql": executed_sql_n,
                    "agent_rows": agent_rows_n,
                    "passed": passed_n,
                    "sql_logs": sql_logs.copy(),
                    "agent_output": noisy_out.get("output", noisy_out),
                    "error": match_err_n,
                }
            )

        except Exception as e:
            robust_results.append(
                {
                    "id": c.id,
                    "original_question": c.question,
                    "noisy_question": noisy_question,
                    "error": str(e),
                }
            )
    # ---- average metrics ----
    avg_query_count = (
        round(statistics.mean(successful_query_counts), 4) if successful_query_counts else 0.0
    )
    avg_latency_sec = (
        round(statistics.mean(successful_latency), 4) if successful_latency else 0.0
    )
    avg_completeness = (
        round(statistics.mean(r["completeness"] for r in results), 4) if results else 0.0
    )
    avg_token_usage = (
        round(statistics.mean(r["token_usage"] for r in results), 4) if results else 0.0
    )

    # ---- Normalize metrics for radar chart ----
    # Query efficiency: 1 query = best, >=4 queries = worst
    query_efficiency = max(0.0, min(1.0, (4 - avg_query_count) / (4 - 1)))

    # Latency efficiency: <=10s best, >=60s worst
    latency_efficiency = max(0.0, min(1.0, (60 - avg_latency_sec) / (60 - 10)))

    # ---- Token efficiency normalization ----
    valid_tokens = [r["token_usage"] for r in results if r["token_usage"] > 0]

    if valid_tokens:
        avg_token_usage = statistics.mean(valid_tokens)
        min_tokens = min(valid_tokens)

        token_efficiency = max(
            0.0,
            min(1.0, min_tokens / avg_token_usage)
        )
    else:
        avg_token_usage = 0.0
        token_efficiency = 0.0

    # robust accuracy: only count cases that were correct on original question
    robust_accuracy = robust_correct / original_correct if original_correct > 0 else 0.0

    summary = {
        "total": len(cases),
        "passed": total_pass,
        "accuracy": round(total_pass / len(cases), 4) if cases else 0.0,
        "result_completeness": avg_completeness,
        "avg_sql_query_count": avg_query_count,
        "avg_latency_sec": avg_latency_sec,
        "query_efficiency": round(query_efficiency, 4),
        "latency_efficiency": round(latency_efficiency, 4),
        "avg_token_usage": avg_token_usage,
        "token_efficiency": round(token_efficiency, 4),
        "robust_accuracy": round(robust_accuracy, 4),
    }

    print("=== SUMMARY ===")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\n=== DETAILS ===")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Optional: save to file for later analysis
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": summary,
                "results": results,
                "robust_results": robust_results
            },
            f,
            indent=2,
            ensure_ascii=False
        )


if __name__ == "__main__":
    main()