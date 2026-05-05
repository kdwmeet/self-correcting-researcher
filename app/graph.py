from typing import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

# 상태 및 검토 스키마 정의
class ResearchState(TypedDict):
    topic: str
    research_data: str
    draft_report: str
    feedback: str
    revision_count: int
    is_acceptable: bool

class ReviewOutput(BaseModel):
    is_acceptable: bool = Field(description="보고서가 기준을 충족하면 True, 보완이 필요하면 False")
    feedback: str = Field(description="보완이 필요한 경우 구체적인 피드백 및 추가 검색 키워드, 통과면 빈 문자열")

# 노드 구현
def research_node(state: ResearchState):
    """웹 검색을 통해 주제에 대한 자료를 수집"""
    search_tool = DuckDuckGoSearchRun()
    topic = state.get("topic", "")
    feedback = state.get("feedback", "")
    current_data = state.get("research_data", "")

    # 피드백이 있다면 피드백을 기반으로 보완 검색, 없다면 메인 주제 검색
    query = feedback if feedback else topic

    try:
        search_result = search_tool.invoke(query)
    except Exception as e:
        search_result = "검색 중 오류 발생: " + str(e)

    new_data = current_data + "\n\n[추가 검색 결과]\n" + search_result
    return {"research_data": new_data}

def draft_node(state: ResearchState):
    """수집된 자료를 바탕으로 보고서 초안을 작성"""
    llm = ChatOpenAI(model="gpt-5.4-nano", reasoning_effort="high")
    topic = state.get("topic", "") 
    research_data = state.get("research_data", "")
    feedback = state.get("feedback", "")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 전문 리서치 분석가입니다. 수집된 자료를 바탕으로 심층 보고서를 작성하십시오. 이전 피드백이 있다면 반드시 반영하여 부족한 부분을 보완하십시오."),
        ("user", "주제: {topic}\n\n수집된 자료: {research_data}\n\n이전 검토 피드백: {feedback}\n\n보고서를 작성하십시오.")
    ])

    response = (prompt | llm).invoke({
        "topic": topic,
        "research_data": research_data,
        "feedback": feedback
    })

    current_count = state.get("revision_count", 0)
    return {"draft_report": response.content, "revision_count": current_count + 1}

def review_node(state: ResearchState):
    """작성된 초안을 검토하고 보완점(피드백)을 도출"""
    llm = ChatOpenAI(model="gpt-5.4-nano", reasoning_effort="high")
    structured_llm = llm.with_structured_output(ReviewOutput)

    topic = state.get("topic", "")
    draft_report = state.get("draft_report", "")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 엄격한 편집장입니다. 작성된 보고서가 주제를 깊이 있게 다루고 있는지 검토하십시오. 정보가 부족하거나 논리가 빈약하면 is_acceptable을 False로 설정하고, 구체적인 추가 검색 키워드 및 피드백을 제공하십시오."),
        ("user", "주제: {topic}\n\n초안 보고서: {draft_report}\n\n검토를 수행하십시오.")
    ])

    result = (prompt | structured_llm).invoke({
        "topic": topic,
        "draft_report": draft_report
    })

    return {
        "is_acceptable": result.is_acceptable,
        "feedback": result.feedback
    }

# 라우팅 조건 함수
def route_review(state: ResearchState):
    """검토 결과에따라 파이프라인을 종료하거나 다시 리서치 단계로 라우팅"""
    is_acceptable = state.get("is_acceptable", False)
    revision_count = state.get("revision_count", 0)

    # 무한 루프 방지를 위해 최대 3회까지만 수정 과정을 거침
    if is_acceptable or revision_count >= 3:
        return END
    return "research"

# 그래프 조립 및 컴파일
workflow = StateGraph(ResearchState)

workflow.add_node("research", research_node)
workflow.add_node("draft", draft_node)
workflow.add_node("review", review_node)

workflow.add_edge(START, "research")
workflow.add_edge("research", "draft")
workflow.add_edge("draft", "review")
workflow.add_conditional_edges("review", route_review, {"research": "research", END: END})

app_graph = workflow.compile()