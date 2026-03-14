import json
import random
from pathlib import Path
import streamlit as st


PAGE_TITLE = "乙級廢棄物練習題庫"
PAGE_ICON = "♻️"


def load_questions(path: str):
    q_path = Path(path)
    if not q_path.is_absolute():
        q_path = Path(__file__).resolve().parent / q_path
    with q_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def init_state():
    if "initialized" in st.session_state:
        return

    questions = load_questions("questions.json")
    random.shuffle(questions)

    st.session_state.initialized = True
    st.session_state.questions = questions
    st.session_state.current_index = 0
    st.session_state.correct_count = 0
    st.session_state.total_answered = 0
    st.session_state.answered_ids = []
    st.session_state.wrong_ids = []
    st.session_state.wrong_id_set = set()
    st.session_state.answer_history = {}
    st.session_state.show_result = False
    st.session_state.result_text = ""
    st.session_state.last_question_id = None
    st.session_state.page_mode = "practice"


def reset_quiz(shuffle_questions: bool = True):
    if shuffle_questions:
        random.shuffle(st.session_state.questions)
    st.session_state.current_index = 0
    st.session_state.correct_count = 0
    st.session_state.total_answered = 0
    st.session_state.answered_ids = []
    st.session_state.wrong_ids = []
    st.session_state.wrong_id_set = set()
    st.session_state.answer_history = {}
    st.session_state.show_result = False
    st.session_state.result_text = ""
    st.session_state.last_question_id = None
    st.session_state.page_mode = "practice"


def get_accuracy() -> float:
    if st.session_state.total_answered == 0:
        return 0.0
    return st.session_state.correct_count / st.session_state.total_answered * 100


def render_sidebar():
    st.sidebar.title("功能選單")

    accuracy = get_accuracy()
    st.sidebar.metric("已作答", st.session_state.total_answered)
    st.sidebar.metric("答對題數", st.session_state.correct_count)
    st.sidebar.metric("正確率", f"{accuracy:.1f}%")
    st.sidebar.metric("錯題數", len(st.session_state.wrong_id_set))

    st.sidebar.markdown("---")
    search_text = st.sidebar.text_input(
        "題目搜尋", placeholder="輸入關鍵字，例如 巴塞爾、公約、掩埋"
    )

    if st.sidebar.button("重新開始全部練習", use_container_width=True):
        reset_quiz(shuffle_questions=True)
        st.rerun()

    if st.sidebar.button("只練錯題", use_container_width=True):
        st.session_state.page_mode = "wrong"
        st.session_state.current_index = 0
        st.session_state.show_result = False
        st.rerun()

    if st.sidebar.button("回到一般練習", use_container_width=True):
        st.session_state.page_mode = "practice"
        st.session_state.current_index = 0
        st.session_state.show_result = False
        st.rerun()

    return search_text


def get_search_results(keyword: str):
    keyword = keyword.strip().lower()
    if not keyword:
        return []

    results = []
    for q in st.session_state.questions:
        haystack = q["question"] + " " + " ".join(q["options"])
        if keyword in haystack.lower():
            results.append(q)
    return results


def render_search_results(keyword: str):
    if not keyword.strip():
        st.info("請先在左側輸入關鍵字搜尋題目。")
        return

    results = get_search_results(keyword)
    st.subheader(f"搜尋結果：{len(results)} 題")

    if not results:
        st.warning("找不到符合關鍵字的題目。")
        return

    for q in results[:50]:
        with st.expander(f"題號 {q.get('q_num', q['id'])}｜{q['question'][:40]}..."):
            st.write(q["question"])
            for idx, option in enumerate(q["options"], start=1):
                marker = "✅" if idx == q["answer"] else ""
                st.write(f"({idx}) {option} {marker}")

    if len(results) > 50:
        st.info(f"結果很多，先顯示前 50 題。共找到 {len(results)} 題。")


def render_wrong_book():
    st.subheader("錯題本")
    wrong_questions = [q for q in st.session_state.questions if q["id"] in st.session_state.wrong_id_set]

    if not wrong_questions:
        st.success("目前還沒有錯題，繼續保持！")
        return

    st.write(f"目前共有 {len(wrong_questions)} 題錯題。")
    for q in wrong_questions:
        user_answer = st.session_state.answer_history.get(q["id"])
        with st.expander(f"題號 {q.get('q_num', q['id'])}｜{q['question'][:40]}..."):
            st.write(q["question"])
            for idx, option in enumerate(q["options"], start=1):
                label = f"({idx}) {option}"
                if idx == q["answer"]:
                    st.write(f"✅ {label}")
                elif user_answer == idx:
                    st.write(f"❌ {label}")
                else:
                    st.write(label)


def get_practice_pool():
    if st.session_state.page_mode == "wrong":
        return [q for q in st.session_state.questions if q["id"] in st.session_state.wrong_id_set]
    return st.session_state.questions


def render_quiz():
    pool = get_practice_pool()

    if not pool:
        if st.session_state.page_mode == "wrong":
            st.success("目前沒有錯題可以複習。")
            return
        st.success("您已完成所有題目！")
        st.write(f"共答對 {st.session_state.correct_count} 題 / 共 {st.session_state.total_answered} 題。")
        return

    if st.session_state.current_index >= len(pool):
        st.success("此模式的題目已作答完成！")
        st.write(f"目前正確率：{get_accuracy():.1f}%")
        if st.button("重新從第一題開始此模式"):
            st.session_state.current_index = 0
            st.session_state.show_result = False
            st.session_state.result_text = ""
            st.rerun()
        return

    q = pool[st.session_state.current_index]
    st.write(f"### 題目 {st.session_state.current_index + 1} / {len(pool)}")
    st.write(q["question"])

    option_labels = [f"({i}) {text}" for i, text in enumerate(q["options"], start=1)]
    selected = st.radio(
        "請選擇答案：",
        options=list(range(1, len(q["options"]) + 1)),
        format_func=lambda idx: option_labels[idx - 1],
        key=f"option_{st.session_state.page_mode}_{q['id']}"
    )

    if st.button("提交答案", key=f"submit_{st.session_state.page_mode}_{q['id']}"):
        st.session_state.total_answered += 1
        st.session_state.answered_ids.append(q["id"])
        st.session_state.answer_history[q["id"]] = selected
        st.session_state.last_question_id = q["id"]

        if selected == q["answer"]:
            st.session_state.correct_count += 1
            st.session_state.result_text = "✅ 恭喜答對！"
            if q["id"] in st.session_state.wrong_id_set and st.session_state.page_mode == "wrong":
                st.session_state.wrong_id_set.remove(q["id"])
                st.session_state.wrong_ids = [x for x in st.session_state.wrong_ids if x != q["id"]]
        else:
            correct_option_text = q["options"][q["answer"] - 1]
            st.session_state.result_text = f"❌ 答錯了。正確答案是 ({q['answer']}) {correct_option_text}"
            if q["id"] not in st.session_state.wrong_id_set:
                st.session_state.wrong_id_set.add(q["id"])
                st.session_state.wrong_ids.append(q["id"])

        st.session_state.show_result = True

    if st.session_state.show_result and st.session_state.last_question_id == q["id"]:
        st.info(st.session_state.result_text)
        if st.button("下一題", key=f"next_{st.session_state.page_mode}_{q['id']}"):
            st.session_state.current_index += 1
            st.session_state.show_result = False
            st.session_state.result_text = ""
            st.session_state.last_question_id = None
            st.rerun()


def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")
    st.title("乙級廢棄物練習題庫 App")
    st.caption("已加入：錯題本、正確率統計、題目搜尋")

    init_state()
    search_text = render_sidebar()

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.page_mode == "wrong":
            st.info("目前模式：錯題複習")
        else:
            st.info("目前模式：一般練習")

    with col2:
        st.progress(min(get_accuracy() / 100, 1.0), text=f"正確率 {get_accuracy():.1f}%")

    tabs = st.tabs(["開始作答", "錯題本", "題目搜尋"])

    with tabs[0]:
        render_quiz()

    with tabs[1]:
        render_wrong_book()

    with tabs[2]:
        render_search_results(search_text)


if __name__ == "__main__":
    main()
