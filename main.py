import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ------------------------------------------------------------
# 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="주가 살펴보기",
    page_icon="🕯️",
    layout="centered",
)

# 따뜻한 톤을 위한 간단한 커스텀 스타일
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF8E7;
    }
    h1, h2, h3 {
        color: #4A3728;
    }
    div[data-testid="stMetric"] {
        background-color: #FFF1CE;
        border: 1px solid #E8B84B;
        border-radius: 14px;
        padding: 14px 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 제목과 설명
# ------------------------------------------------------------
st.title("🕯️ 주가 살펴보기")
st.write(
    "종목 코드를 입력하면 최근 1년간의 주가 흐름을 그래프로 보여드려요. "
    "예시: **AAPL** (애플), **005930.KS** (삼성전자), **035420.KS** (네이버)"
)

# ------------------------------------------------------------
# 종목 코드 입력창
# ------------------------------------------------------------
ticker_input = st.text_input(
    "종목 코드를 입력하세요",
    value="AAPL",
    placeholder="예: AAPL, 005930.KS",
    help="한국 주식은 코드 뒤에 .KS(코스피) 또는 .KQ(코스닥)를 붙여주세요.",
)

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (종목 코드는 보통 대문자)
ticker = ticker_input.strip().upper()


# ------------------------------------------------------------
# 주가 데이터를 가져오는 함수
# yfinance 호출은 시간이 걸리므로 캐시를 사용해서
# 같은 종목을 반복 조회할 때 속도를 높여줍니다.
# ------------------------------------------------------------
@st.cache_data(ttl=60 * 60)  # 1시간 동안 캐시 유지
def load_price_history(code: str):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)  # 최근 1년

    data = yf.download(
        code,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        progress=False,
    )
    return data


# ------------------------------------------------------------
# 회사 이름을 가져오는 함수 (실패해도 앱이 멈추지 않도록 예외 처리)
# ------------------------------------------------------------
@st.cache_data(ttl=60 * 60)
def load_company_name(code: str):
    try:
        info = yf.Ticker(code).info
        return info.get("longName") or info.get("shortName") or code
    except Exception:
        return code


# ------------------------------------------------------------
# 종목 코드가 입력되었을 때만 아래 내용을 실행
# ------------------------------------------------------------
if ticker:
    with st.spinner(f"'{ticker}' 데이터를 불러오는 중이에요..."):
        history = load_price_history(ticker)

    # 데이터가 비어 있으면 잘못된 종목 코드일 가능성이 큼
    if history is None or history.empty:
        st.error(
            "데이터를 찾을 수 없어요. 종목 코드를 다시 확인해주세요. "
            "(한국 주식은 .KS 또는 .KQ를 붙여야 해요)"
        )
    else:
        company_name = load_company_name(ticker)
        st.subheader(f"📈 {company_name} ({ticker})")

        # 종가(Close) 컬럼만 사용
        close_prices = history["Close"]

        # 종목 코드가 여러 컬럼(멀티인덱스)으로 올 경우를 대비한 안전 처리
        if hasattr(close_prices, "columns"):
            close_prices = close_prices.iloc[:, 0]

        current_price = float(close_prices.iloc[-1])
        start_price = float(close_prices.iloc[0])
        change_amount = current_price - start_price
        change_percent = (change_amount / start_price) * 100

        # ------------------------------------------------------------
        # 지표 카드: 현재가, 1년 등락률
        # ------------------------------------------------------------
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="현재가",
                value=f"{current_price:,.2f}",
            )

        with col2:
            st.metric(
                label="최근 1년 등락률",
                value=f"{change_percent:+.2f}%",
                delta=f"{change_amount:+,.2f}",
            )

        # ------------------------------------------------------------
        # Plotly 꺾은선 그래프
        # ------------------------------------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=close_prices.index,
                y=close_prices.values,
                mode="lines",
                name="종가",
                line=dict(color="#E07A5F", width=2),
                fill="tozeroy",
                fillcolor="rgba(224, 122, 95, 0.12)",
            )
        )

        fig.update_layout(
            title="최근 1년 주가 흐름",
            xaxis_title="날짜",
            yaxis_title="가격",
            plot_bgcolor="#FFF8E7",
            paper_bgcolor="#FFF8E7",
            font=dict(color="#4A3728"),
            hovermode="x unified",
            margin=dict(l=20, r=20, t=50, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "데이터 출처: Yahoo Finance (yfinance). "
            "투자 참고용 정보이며 투자 판단의 책임은 본인에게 있습니다."
        )
else:
    st.info("종목 코드를 입력하면 결과가 여기에 표시돼요.")
