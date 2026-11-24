from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import get_settings
from app.rag.state import AgentState, RouteDecision
from app.rag.vectorstore import get_retriever

from app.rag.state import EvidenceGrade
from langchain_tavily import TavilySearch

from typing import Literal

from langgraph.graph import StateGraph, START, END

settings = get_settings()


llm = ChatGroq(
    model=settings.groq_model,
    api_key=settings.groq_api_key,
    temperature=0
)


router_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen kurumsal IT destek sisteminin soru yönlendirme
        bileşenisin.

        Kullanıcının sorusunu analiz et.

        Eğer soru şirket politikaları, IT destek,
        teknik sorunlar veya şirket dokümanlarıyla ilgiliyse
        kb seç.

        Eğer soru selamlama, teşekkür veya genel sohbet
        niteliğindeyse direct seç.

        Yalnızca tanımlanan seçeneklerden birini döndür.
        """
    ),
    ("human", "{question}")
])


router_chain = router_prompt | llm.with_structured_output(
    RouteDecision
)


def route_question(state: AgentState) -> dict:

    decision = router_chain.invoke({
        "question": state["question"]
    })

    return {
    "source_used": decision.route,
    "trace": state.get("trace", []) + [
        f"Router selected: {decision.route}"
    ]
}


def retrieve_kb(state: AgentState) -> dict:

    retriever = get_retriever()

    docs = retriever.invoke(state["current_query"])

    return {
        "kb_docs": docs,
        "trace": state.get("trace", []) + [
            f"Retrieved {len(docs)} documents from knowledge base"
        ]
    }


grade_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen kurumsal IT destek sisteminin kanıt değerlendirme
        bileşenisin.

        Kullanıcının sorusunu ve bilgi tabanından getirilen
        dokümanları değerlendir.

        Dokümanlar soruyu cevaplamak için yeterli ve ilgiliyse
        good, yeterli değilse weak sonucunu döndür.

        Yalnızca tanımlanan seçeneklerden birini döndür.
        """
    ),
    (
        "human",
        """
        Kullanıcı sorusu:
        {question}

        Getirilen dokümanlar:
        {context}
        """
    )
])


grade_chain = grade_prompt | llm.with_structured_output(
    EvidenceGrade
)


def grade_kb(state: AgentState) -> dict:

    context = "\n\n".join(
        doc.page_content
        for doc in state["kb_docs"]
    )

    grade = grade_chain.invoke({
        "question": state["question"],
        "context": context
    })

    return {
        "kb_grade": grade.grade,
        "trace": state.get("trace", []) + [
            f"Knowledge base grade: {grade.grade}"
        ]
    }


web_search = TavilySearch(
    max_results=5,
    topic="general",
    tavily_api_key=settings.tavily_api_key
)


def search_web(state: AgentState) -> dict:

    results = web_search.invoke({
        "query": state["current_query"]
    })

    if isinstance(results, dict):
        web_results = results.get("results", [])

        context = "\n\n".join(
            f"Başlık: {item.get('title', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"İçerik: {item.get('content', '')}"
            for item in web_results
        )

        citations = [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "type": "web"
            }
            for item in web_results
        ]

    else:
        context = str(results)
        citations = []

    return {
        "web_results": context,
        "citations": citations,
        "trace": state.get("trace", []) + [
            "Web search completed using Tavily"
        ]
    }


web_grade_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen kurumsal IT destek sisteminin web kanıtı
        değerlendirme bileşenisin.

        Kullanıcının sorusunu ve web arama sonuçlarını değerlendir.

        Sonuçlar soruyu cevaplamak için yeterli ve ilgiliyse
        good, yeterli değilse weak sonucunu döndür.

        Yalnızca tanımlanan seçeneklerden birini döndür.
        """
    ),
    (
        "human",
        """
        Kullanıcı sorusu:
        {question}

        Web arama sonuçları:
        {context}
        """
    )
])


web_grade_chain = web_grade_prompt | llm.with_structured_output(
    EvidenceGrade
)


def grade_web(state: AgentState) -> dict:

    grade = web_grade_chain.invoke({
        "question": state["question"],
        "context": state["web_results"]
    })

    return {
        "web_grade": grade.grade,
        "trace": state.get("trace", []) + [
            f"Web search grade: {grade.grade}"
        ]
    }


rewrite_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen kurumsal IT destek sisteminin sorgu yeniden yazma
        bileşenisin.

        Kullanıcının sorusunu analiz et ve daha iyi arama
        sonuçları elde etmek için yeniden düzenle.

        Sorunun temel anlamını koru.
        Teknik anahtar kelimeleri kullan.
        Gereksiz açıklama ekleme.
        Yalnızca yeniden yazılmış sorguyu döndür.
        """
    ),
    ("human", "{question}")
])


rewrite_chain = rewrite_prompt | llm


def rewrite_query(state: AgentState) -> dict:

    response = rewrite_chain.invoke({
        "question": state["current_query"]
    })

    rewritten_query = response.content.strip()

    return {
        "current_query": rewritten_query,
        "retry_count": state.get("retry_count", 0) + 1,
        "trace": state.get("trace", []) + [
            f"Query rewritten: {rewritten_query}"
        ]
    }


generate_kb_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen Türkçe yanıt veren kurumsal IT destek asistanısın.

        Kullanıcının sorusunu yalnızca verilen şirket
        dokümanlarına dayanarak cevapla.

        Açık, anlaşılır ve uygulanabilir adımlar sun.
        Dokümanlarda bulunmayan bilgileri uydurma.
        Cevabını Türkçe oluştur.
        """
    ),
    (
        "human",
        """
        Kullanıcı sorusu:
        {question}

        Şirket dokümanları:
        {context}
        """
    )
])

generate_kb_chain = generate_kb_prompt | llm


def generate_from_kb(state: AgentState) -> dict:

    context = "\n\n".join(
        doc.page_content
        for doc in state["kb_docs"]
    )

    response = generate_kb_chain.invoke({
        "question": state["question"],
        "context": context
    })

    return {
        "answer": response.content,
        "source_used": "private_kb",
        "trace": state.get("trace", []) + [
            "Answer generated from company knowledge base"
        ]
    }


generate_web_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Sen Türkçe yanıt veren kurumsal IT destek asistanısın.

        Kullanıcının sorusunu verilen web arama sonuçlarına
        dayanarak cevapla.

        Web kaynaklarının harici kaynaklar olduğunu belirt.
        Kanıtlarda bulunmayan bilgileri uydurma.
        Cevabını Türkçe oluştur.
        """
    ),
    (
        "human",
        """
        Kullanıcı sorusu:
        {question}

        Web arama sonuçları:
        {context}
        """
    )
])

generate_web_chain = generate_web_prompt | llm


def generate_from_web(state: AgentState) -> dict:

    response = generate_web_chain.invoke({
        "question": state["question"],
        "context": state["web_results"]
    })

    return {
        "answer": response.content,
        "source_used": "web_search",
        "trace": state.get("trace", []) + [
            "Answer generated from web search"
        ]
    }


def direct_answer(state: AgentState) -> dict:

    response = llm.invoke(
        f"""
        Sen Türkçe konuşan yardımcı bir asistansın.
        Kullanıcının mesajına doğal ve kısa bir yanıt ver.

        Kullanıcı mesajı:
        {state['question']}
        """
    )

    return {
        "answer": response.content,
        "source_used": "direct",
        "trace": state.get("trace", []) + [
            "Direct answer generated"
        ]
    }


def insufficient(state: AgentState) -> dict:

    return {
        "answer": (
            "Bu soruyu güvenilir şekilde yanıtlamak için "
            "yeterli bilgi bulamadım. Lütfen IT destek "
            "ekibiyle iletişime geçin veya sorun hakkında "
            "daha fazla bilgi sağlayın."
        ),
        "source_used": "insufficient_evidence",
        "trace": state.get("trace", []) + [
            "Insufficient evidence to generate an answer"
        ]
    }


def route_after_router(
    state: AgentState
) -> Literal["retrieve_kb", "direct_answer"]:

    if state["source_used"] == "kb":
        return "retrieve_kb"

    return "direct_answer"


def after_kb(
    state: AgentState
) -> Literal["generate_from_kb", "search_web"]:

    if state["kb_grade"] == "good":
        return "generate_from_kb"

    return "search_web"


def after_web(
    state: AgentState
) -> Literal["generate_from_web", "rewrite_query", "insufficient"]:

    if state["web_grade"] == "good":
        return "generate_from_web"

    if state["retry_count"] < settings.max_retries:
        return "rewrite_query"

    return "insufficient"


def build_graph():

    graph = StateGraph(AgentState)

    graph.add_node("route_question", route_question)
    graph.add_node("retrieve_kb", retrieve_kb)
    graph.add_node("grade_kb", grade_kb)
    graph.add_node("search_web", search_web)
    graph.add_node("grade_web", grade_web)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("generate_from_kb", generate_from_kb)
    graph.add_node("generate_from_web", generate_from_web)
    graph.add_node("direct_answer", direct_answer)
    graph.add_node("insufficient", insufficient)

    graph.add_edge(START, "route_question")

    graph.add_conditional_edges(
        "route_question",
        route_after_router,
        {
            "retrieve_kb": "retrieve_kb",
            "direct_answer": "direct_answer"
        }
    )

    graph.add_edge("retrieve_kb", "grade_kb")

    graph.add_conditional_edges(
        "grade_kb",
        after_kb,
        {
            "generate_from_kb": "generate_from_kb",
            "search_web": "search_web"
        }
    )

    graph.add_edge("search_web", "grade_web")

    graph.add_conditional_edges(
        "grade_web",
        after_web,
        {
            "generate_from_web": "generate_from_web",
            "rewrite_query": "rewrite_query",
            "insufficient": "insufficient"
        }
    )

    graph.add_edge("rewrite_query", "retrieve_kb")

    graph.add_edge("generate_from_kb", END)
    graph.add_edge("generate_from_web", END)
    graph.add_edge("direct_answer", END)
    graph.add_edge("insufficient", END)

    return graph.compile()


agent_graph = build_graph()


def ask(question: str) -> dict:

    initial_state: AgentState = {
        "question": question,
        "current_query": question,
        "source_used": "",
        "kb_docs": [],
        "web_results": "",
        "kb_grade": "",
        "web_grade": "",
        "answer": "",
        "retry_count": 0,
        "trace": [],
        "citations": []
    }

    return agent_graph.invoke(initial_state)


