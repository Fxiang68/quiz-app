
import json
import random
from pathlib import Path
import streamlit as st

PAGE_TITLE = "乙級廢棄物練習題庫"
PAGE_ICON = "♻️"

# Load questions from JSON file
def load_questions(path: str):
    q_path = Path(path)
    if not q_path.is_absolute():
        q_path = Path(__file__).resolve().parent / q_path
    with q_path.open("r", encoding="utf-8") as f:
        return json.load(f)

# Initialize session state
def init_state():
    if "initialized" in st.session_state:
        return

    chapter_path = "questions_by_chapter_final.json"  # Correct path to the final JSON file
    questions_by_chapter = load_questions(chapter_path)

    st.session_state.initialized = True
    st.session_state.questions_by_chapter = questions_by_chapter
    st.session_state.current_chapter = None
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

# Reset quiz to the beginning
def reset_quiz():
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

# Get accuracy
def get_accuracy() -> float:
    if st.session_state.total_answered == 0:
        return 0.0
    return st.session_state.correct_count / st.session_state.total_answered * 100

# Sidebar menu for chapter selection
def render_sidebar():
    st.sidebar.title("選擇練習的冊數")
    chapter_titles = list(st.session_state.questions_by_chapter.keys())

    # Display chapter selection
    chapter_selection = st.sidebar.selectbox("選擇練習的冊數", chapter_titles)
    st.session_state.current_chapter = chapter_selection

    # Display stats
    accuracy = get_accuracy()
    st.sidebar.metric("已作答", st.session_state.total_answered)
    st.sidebar.metric("答對題數", st.session_state.correct_count)
    st.sidebar.metric("正確率", f"{accuracy:.1f}%")
    st.sidebar.metric("錯題數", len(st.session_state.wrong_id_set))

    # Search bar for question search
    search_text = st.sidebar.text_input("題目搜尋", placeholder="輸入關鍵字，例如 巴塞爾、公約、掩埋")

    # Control buttons
    if st.sidebar.button("重新開始", use_container_width=True):
        reset_quiz()
        st.rerun()

    return search_text

# Get questions from the selected chapter
def get_chapter_questions():
    chapter = st.session_state.current_chapter
    if chapter and chapter in st.session_state.questions_by_chapter:
        return st.session_state.questions_by_chapter[chapter]
    return []

# Get search results based on input keyword
def get_search_results(keyword: str):
    keyword = keyword.strip().lower()
    if not keyword:
        return []

    results = []
    for q in get_chapter_questions():
        haystack = q["question"] + " " + " ".join(q["options"])
        if keyword in haystack.lower():
            results.append(q)
    return results

# Render search results
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

# Render wrong book
def render_wrong_book():
    st.subheader("錯題本")
    # Ensure that wrong_ids are valid and that questions exist
    wrong_questions = [q for q in get_chapter_questions() if q["id"] in st.session_state.wrong_id_set]

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
