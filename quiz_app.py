import json
import random
from pathlib import Path
import streamlit as st


def load_questions(path: str):
    """
    Load questions from a JSON file.  Each question is expected to be a
    dictionary with the keys: 'id', 'q_num', 'question', 'options', and
    'answer' (1-based index of correct option).

    Parameters
    ----------
    path : str
        Path to the JSON file containing the question bank.

    Returns
    -------
    list
        A list of question dictionaries.
    """
    q_path = Path(path)
    # If path is relative, treat it as relative to this file's directory
    if not q_path.is_absolute():
        q_path = Path(__file__).resolve().parent / q_path
    with q_path.open('r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def initialize_state():
    """Initialize Streamlit session state on first run."""
    if 'initialized' not in st.session_state:
        # Load questions once and shuffle to randomize order
        st.session_state.questions = load_questions('questions.json')
        random.shuffle(st.session_state.questions)
        st.session_state.current_index = 0
        st.session_state.correct_count = 0
        st.session_state.total_answered = 0
        st.session_state.show_result = False
        st.session_state.result_text = ''
        st.session_state.initialized = True


def main():
    """Main function to run the quiz app."""
    st.set_page_config(page_title="乙級廢棄物練習題庫", page_icon="♻️")
    st.title("乙級廢棄物練習題庫 App")
    st.markdown(
        """
        使用下列題庫可以進行自我練習。選擇一個答案並點選「提交答案」，
        系統會立即告知是否答對，並可繼續下一題。題目來源為考試練習題，
        用於個人練習用途。
        """
    )
    initialize_state()

    # When all questions have been answered, show summary and reset option
    if st.session_state.current_index >= len(st.session_state.questions):
        st.success("您已完成所有題目！")
        st.write(f"共答對 {st.session_state.correct_count} 題 / 共 {st.session_state.total_answered} 題。")
        if st.button("重新開始練習"):
            random.shuffle(st.session_state.questions)
            st.session_state.current_index = 0
            st.session_state.correct_count = 0
            st.session_state.total_answered = 0
            st.session_state.show_result = False
            st.session_state.result_text = ''
        return

    # Get current question
    q = st.session_state.questions[st.session_state.current_index]
    st.write(f"### 題目 {st.session_state.current_index + 1} / {len(st.session_state.questions)}")
    st.write(q['question'])

    # Present options using radio buttons.  The radio returns the label (1–4) and we map it back.
    option_labels = [f"({i}) {text}" for i, text in enumerate(q['options'], start=1)]
    # Use a unique key per question to preserve state across reruns
    selected = st.radio(
        "請選擇答案：",
        options=list(range(1, len(q['options']) + 1)),
        format_func=lambda idx: option_labels[idx - 1],
        key=f"option_{st.session_state.current_index}"
    )

    # Submit answer button
    if st.button("提交答案", key=f"submit_{st.session_state.current_index}"):
        st.session_state.total_answered += 1
        if selected == q['answer']:
            st.session_state.correct_count += 1
            st.session_state.result_text = "✅ 恭喜答對！"
        else:
            correct_option_text = q['options'][q['answer'] - 1]
            st.session_state.result_text = (
                f"❌ 答錯了。正確答案是 ({q['answer']}) {correct_option_text}"
            )
        st.session_state.show_result = True

    # Show result if applicable and allow moving to next question
    if st.session_state.show_result:
        st.info(st.session_state.result_text)
        if st.button("下一題", key=f"next_{st.session_state.current_index}"):
            st.session_state.current_index += 1
            st.session_state.show_result = False
            st.session_state.result_text = ''
            # Reset radio selection for next question by clearing the key
            try:
                del st.session_state[f"option_{st.session_state.current_index - 1}"]
            except KeyError:
                pass


if __name__ == '__main__':
    main()