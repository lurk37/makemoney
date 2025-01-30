import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from glob import glob

# 페이지 기본 설정
st.set_page_config(
    page_title="주식 정보 대시보드",
    page_icon="📈",
    layout="wide"
)

# CSV 파일 읽기 부분
def get_latest_csv():
    csv_files = glob(os.path.join('.', 'sise_csv', '*.csv'))
    if not csv_files:
        raise FileNotFoundError('sise_csv 폴더에 CSV 파일이 없습니다.')
    latest_file = max(csv_files, key=os.path.getctime)
    
    try:
        date_str = latest_file.split('_')[-2]  # 20241230
        time_str = latest_file.split('_')[-1].replace('.csv', '')  # 215134
        
        formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일"
        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
        trading_date = f"{formatted_date} {formatted_time}"
    except:
        trading_date = "날짜 형식 변환 실패"
    
    return latest_file, trading_date

def get_company_info_and_news(종목코드, 종목명):
    url = f"https://finance.naver.com/item/main.naver?code={종목코드}"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        summary = soup.find('div', {'class': 'summary_info'}).get_text(strip=True)
    except AttributeError:
        summary = "기업 요약 정보를 찾을 수 없습니다."
    
    news_url = f"https://search.naver.com/search.naver?where=news&query={종목명}"
    news_response = requests.get(news_url)
    news_soup = BeautifulSoup(news_response.text, 'html.parser')
    
    news_list = []
    for news_item in news_soup.find_all('a', {'class': 'news_tit'}, limit=5):
        news_title = news_item.get_text(strip=True)
        news_link = news_item['href']
        news_list.append((news_title, news_link))
    
    return summary, news_list

def get_all_trading_dates():
    csv_files = glob(os.path.join('.', 'sise_csv', '*.csv'))
    if not csv_files:
        raise FileNotFoundError('sise_csv 폴더에 CSV 파일이 없습니다.')
    
    dates = []
    for file in csv_files:
        try:
            date_str = file.split('_')[-2]
            time_str = file.split('_')[-1].replace('.csv', '')
            
            formatted_date = f"{date_str[:4]}년 {date_str[4:6]}월 {date_str[6:]}일 {time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
            dates.append({
                'display': formatted_date,
                'filename': file,
                'timestamp': f"{date_str}_{time_str}"
            })
        except:
            continue
    
    dates.sort(key=lambda x: x['timestamp'], reverse=True)
    return dates

def main():
    st.title("📈 주식 정보 대시보드")
    
    with st.sidebar:
        st.header("검색 및 필터")
        
        # 사이드바에 날짜 선택 옵션 추가
        trading_dates = get_all_trading_dates()
        date_options = {date['display']: date['filename'] for date in trading_dates}
        selected_date_display = st.selectbox(
            '거래일자 선택',
            options=list(date_options.keys())
        )
        
        # 검색 기능
        search_query = st.text_input('종목명 검색')
    
    selected_file = date_options[selected_date_display]
    
    # CSV 파일 읽기
    df = pd.read_csv(selected_file, dtype={'종목코드': str})
    df['종목명'] = df['종목명'].astype(str)
    
    # 검색어로 필터링
    if search_query:
        filtered_df = df[df['종목명'].str.contains(search_query, case=False)]
    else:
        filtered_df = df
    
    st.header(f"거래일자: {selected_date_display}")
    
    # 데이터프레임 표시
    with st.expander("주식 데이터 테이블", expanded=True):
        st.dataframe(
            filtered_df.style.format({
                '현재가': '{:,.0f}',
                '거래량': '{:,.0f}',
                'PER': '{:.2f}',
                '시가': '{:,.0f}',
                '고가': '{:,.0f}',
                '저가': '{:,.0f}'
            }),
            height=400
        )
    
    # 선택된 종목 상세 정보 표시
    if not filtered_df.empty:
        st.header("종목 상세 정보")
        for index, row in filtered_df.iterrows():
            종목코드 = str(row['종목코드']).zfill(6)
            종목명 = row['종목명']
            
            with st.expander(f"{종목명} ({종목코드})"):
                # 주가 정보 섹션
                st.subheader("주가 정보")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("현재가", f"{row['현재가']:,}원", 
                             delta=f"{((row['현재가']-row['시가'])/row['시가']*100):.1f}%")
                with col2:
                    st.metric("거래량", f"{row['거래량']:,}")
                with col3:
                    st.metric("PER", f"{row['PER']:.2f}")
                
                # 가격 범위 정보
                st.subheader("가격 범위")
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("시가", f"{row['시가']:,}원")
                with col5:
                    st.metric("고가", f"{row['고가']:,}원")
                with col6:
                    st.metric("저가", f"{row['저가']:,}원")
                
                # 기업 요약과 뉴스 정보 가져오기
                summary, news_list = get_company_info_and_news(종목코드, 종목명)
                
                # 기업 요약 섹션
                st.subheader("기업 개요")
                st.write(summary)
                
                # 뉴스 섹션
                st.subheader("관련 뉴스")
                for news_title, news_link in news_list:
                    st.write(f"[{news_title}]({news_link})")

if __name__ == '__main__':
    main()
