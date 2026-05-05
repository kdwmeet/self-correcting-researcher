import streamlit as st
from app.graph import app_graph

st.set_page_config(page_title="자가 수정 리서치 에이전트", layout="wide")

st.title("자가 수정(Self-Correction) 심층 리서치 에이전트")
st.markdown("에이전트가 외부 웹 검색을 통해 자료를 수집하고 보고서를 작성한 뒤, 스스로 품질을 검토합니다. 기준에 미달하면 피드백을 생성하고 추가 리서치 및 수정을 반복하는 순환형 아키텍처입니다.")
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("리서치 주제 입력")
    with st.form("research_form"):
        topic_input = st.text_input(
            "조사할 주제를 입력하십시오.",
            placeholder="예: 최신 생성형 AI모델의 구조적 한계와 해결 방안"
        )
        submit_btn = st.form_submit_button("심층 리서치 시작", use_container_width=True)

with col2:
    st.subheader("파이프라인 실행 현황")

    if submit_btn and topic_input.strip():
        initial_state = {
            "topic": topic_input,
            "research_data": "",
            "draft_report": "",
            "feedback": "",
            "revision_count": 0,
            "is_acceptable": False
        }

        final_report = ""

        with st.container(border=True):
            with st.spinner("순환형 리서치 파이프 라인을 가동 합니다..."):
                for output in app_graph.stream(initial_state):
                    if not output:
                        continue

                    for node_name, state_update in output.items():
                        if not state_update:
                            continue

                        if node_name == "research":
                            st.markdown("**[1. 리서치 노드]** 외부 웹 검색을 통해 데이터를 수집했습니다.")
                        elif node_name == "draft":
                            final_report = state_update.get("draft_report", "")
                            count = state_update.get("revision_count", 0)
                            st.markdown(f"**[2. 작성 노드]** {count}번쨰 보고서 초안 작성을 완료했습니다.")
                        elif node_name == "review":
                            is_acceptable = state_update.get("is_acceptable", False)
                            feedback = state_update.get("feedback", "")

                            if is_acceptable:
                                st.success("**[3. 검토 노드]** 보고서 품질이 기준을 통과햇습니다. 파이프라인을 종료합니다.")
                            else:
                                st.warning(f"**[3. 검토 노드]** 품질 미달로 재작업을 지시합니다.\n 피드백: {feedback}")
                        
                        st.divider()

        st.subheader("최종 심층 보고서")
        if final_report:
            st.markdown(final_report)

    elif not submit_btn:
        st.info("좌측에 주제를 입력하고 파이프라인을 가동하십시오.")