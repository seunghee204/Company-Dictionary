import streamlit as st
import pandas as pd
import re

# 페이지 설정
# 로컬 이미지 파일(icon.png)을 직접 지정하여 모바일 홈 화면 아이콘을 완벽하게 오버라이드함
st.set_page_config(page_title="사내 약어 사전", page_icon="icon.png", layout="centered", initial_sidebar_state="collapsed")

# 모바일 친화적인 CSS 적용 (다크모드 호환을 위해 고정 색상 제거)
st.markdown("""
    <style>
    /* 입력창에 소문자로 입력해도 대문자로 보이게 처리 */
    input[type="text"] {
        text-transform: uppercase !important;
        font-weight: bold;
    }
    
    /* 모바일용 세로 카드 스타일 */
    .result-card {
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 16px;
        background-color: transparent; /* 다크모드 호환을 위해 투명 처리 */
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        line-height: 1.5;
    }
    .abbrev-title {
        margin: 0 0 12px 0;
        font-size: 24px;
        color: #1f77b4; /* 파란색은 양쪽 모드에서 잘보임 */
        font-weight: 800;
        border-bottom: 2px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 8px;
    }
    .result-text {
        margin: 8px 0;
        font-size: 16px;
        color: inherit; /* 다크모드에서 흰색, 라이트모드에서 검은색 자동 상속 */
    }
    .result-label {
        font-weight: 700;
        color: #6c757d; /* 회색 라벨 유지 */
        display: inline-block;
        width: 45px;
    }
    .kor-text {
        color: #d62728; /* 빨간색 포인트 유지 */
        font-weight: 700;
    }
    
    /* 하이라이트 글씨는 다크/라이트 모드 범용적인 연한 노란색 렌더링 */
    .highlight {
        background-color: rgba(250, 204, 21, 0.5);
        font-weight: bold;
        border-radius: 3px;
        padding: 0 4px;
    }
    
    /* 스트림릿 특유의 화면 전환(사라질 때 흐려지는) 애니메이션 완벽한 강제 삭제 */
    * {
        transition: opacity 0s !important;
        animation-duration: 0s !important;
    }
    
    /* 하단 여백 추가 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 80px;
    }
    </style>
""", unsafe_allow_html=True)

# 검색어 하이라이트 함수
def highlight_text(text, query):
    if not query or not str(text).strip():
        return text
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(r"<span class='highlight'>\1</span>", str(text))

# ================= 사내 보안 방어막 (로그인) =================
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

login_placeholder = st.empty()

if not st.session_state['authenticated']:
    with login_placeholder.container():
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>🔒 사내 보안 접속</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.6; margin-bottom: 30px;'>이 앱은 회사 내부 전용입니다. 공용 비밀번호를 입력해주세요.</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            pwd = st.text_input("비밀번호", type="password", label_visibility="collapsed", placeholder="비밀번호 입력")
            login_btn = st.form_submit_button("접속하기", type="primary", use_container_width=True)
            
            if login_btn:
                if pwd.strip() == "CS0000":
                    st.session_state['authenticated'] = True
                    login_placeholder.empty()
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()
# =========================================================

st.markdown("<h1 class='app-title'>🔍 사내 약어 사전</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return pd.read_csv('translated_abbreviations.csv')

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 파일에 문제가 있습니다: {e}")
    st.stop()

# ================= 메인 네비게이션 (라디오 버튼 대신 책갈피 탭 2개 사용) =================
tab1, tab2 = st.tabs(["✅ 검색 모드", "🔠 알파벳 인덱스 (A-Z)"])

with tab1:
    # ---------------- 1. 단어 검색 모드 ----------------
    with st.form("search_form"):
        search_query = st.text_input("🔍 찾고 싶은 단어를 입력하세요", "", placeholder="예: 1CWBA")
        submitted = st.form_submit_button("검색하기", type="primary", use_container_width=True)

    if submitted and search_query.strip():
        sq = search_query.strip()
        
        # 1. 약어가 대소문자 무시하고 '정확히' 일치하는 단어 찾기
        exact_abbrev_df = df[df['약어'].astype(str).str.upper() == sq.upper()]
        
        if not exact_abbrev_df.empty:
            filtered_df = exact_abbrev_df
        else:
            # 2. 정확히 없으면 부분 일치 검색
            filtered_df = df[
                df['약어'].astype(str).str.contains(sq, case=False, na=False) |
                df['영문/원문'].astype(str).str.contains(sq, case=False, na=False) |
                df['한글 해석'].astype(str).str.contains(sq, case=False, na=False)
            ]
        
        if not filtered_df.empty:
            st.success(f"✨ 총 {len(filtered_df)}개의 결과를 찾았습니다.")
            
            for _, row in filtered_df.iterrows():
                abbrev = str(row['약어']) if pd.notnull(row['약어']) else ""
                eng = str(row['영문/원문']) if pd.notnull(row['영문/원문']) else ""
                kor = str(row['한글 해석']) if pd.notnull(row['한글 해석']) else ""
                
                # 하이라이트 적용
                abbrev_hl = highlight_text(abbrev, sq)
                eng_hl = highlight_text(eng, sq)
                kor_hl = highlight_text(kor, sq)
                
                # 원문과 해석이 같으면 해석란 숨김
                if eng.strip().lower() == kor.strip().lower():
                    kor_html = ""
                else:
                    kor_html = f'<div class="result-text"><span class="result-label">해석:</span> <span class="kor-text">{kor_hl}</span></div>'
                
                st.markdown(f"""
                <div class="result-card">
                    <div class="abbrev-title">{abbrev_hl}</div>
                    <div class="result-text"><span class="result-label">원문:</span> {eng_hl}</div>
                    {kor_html}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("❌ 일치하는 결과가 없습니다. 다른 단어를 검색해 보세요.")
    else:
        st.info("👆 약어나 해석 키워드를 입력하고 검색을 시작하세요.")

with tab2:
    # ---------------- 2. 알파벳별 찾아보기 모드 ----------------
    st.markdown("#### 🔠 첫 글자로 찾아보기")
    
    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ#")
    alpha_tabs = st.tabs(letters)
    
    for i, a_tab in enumerate(alpha_tabs):
        with a_tab:
            char = letters[i]
            if char == '#':
                condition = df['약어'].astype(str).str.match(r'^[^A-Za-z]', na=False)
            else:
                condition = df['약어'].astype(str).str.upper().str.startswith(char, na=False)
                
            tab_df = df[condition]
            
            if tab_df.empty:
                st.write("해당하는 약어가 없습니다.")
            else:
                # 탭마다 많은 약어가 쏟아지지 않도록 일부만 표기하고 세로 스크롤 컨테이너 사용
                with st.container(height=500, border=False):
                    for _, row in tab_df.head(100).iterrows():
                        abbrev = str(row['약어']) if pd.notnull(row['약어']) else ""
                        eng = str(row['영문/원문']) if pd.notnull(row['영문/원문']) else ""
                        kor = str(row['한글 해석']) if pd.notnull(row['한글 해석']) else ""
                        
                        kor_str = "" if eng.strip().lower() == kor.strip().lower() else f" / <span style='color: #d62728; font-weight: 600;'>{kor}</span>"
                        st.markdown(f"**{abbrev}** : {eng} {kor_str}", unsafe_allow_html=True)
                        st.divider()
