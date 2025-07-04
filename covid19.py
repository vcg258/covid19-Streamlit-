import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title='코로나19 한국 대시보드', layout='wide', page_icon='📈')
st.title('KR 코로나19 한국 감염자 대시보드')

# 파일 업로드 - csv파일만
uploaded_confirmed = st.file_uploader('확진자 CSV 업로드', type=['csv'])
uploaded_deaths = st.file_uploader('사망자 CSV 업로드', type=['csv'])
uploaded_recovered = st.file_uploader('회복자 CSv 업로드', type=['csv'])

# 모든 파일이 업로드 되었다면 실행
if uploaded_confirmed and uploaded_deaths and uploaded_recovered:
    # csv파일 내용 읽어서 데이터프레임으로
    df_confirmed = pd.read_csv(uploaded_confirmed) # 확진자 데이터프레임
    df_deaths = pd.read_csv(uploaded_deaths) # 사망자 데이터프레임
    df_recovered = pd.read_csv(uploaded_recovered) # 회복자 데이터프레임

    # 함수 정의 - 대한민국 데이터만 추출, 날짜형식도 대한민국 스타일로
    # 매개변수 df -> 데이터 프레임, value_name -> 확진자, 사망자, 회복자
    def get_korea_data(df, value_name):
        korea_df = df[df['Country/Region'] == 'Korea, South']
        korea_df = korea_df.drop(columns=['Province/State', 'Country/Region', 'Lat', 'Long'])
        korea_series = korea_df.sum().reset_index()
        korea_series.columns = ['날짜', value_name]
        # 날짜 형식을 datetime으로 변환
        korea_series['날짜'] = pd.to_datetime(korea_series['날짜'], format='%m/%d/%y')
        return korea_series

    df_confirmed = get_korea_data(df_confirmed, '확진자')
    df_deaths = get_korea_data(df_deaths, '사망자')
    df_recovered = get_korea_data(df_recovered, '회복자')

    # 데이터 병합
    df_merged = df_confirmed.merge(df_deaths, on='날짜').merge(df_recovered, on='날짜')

    # 날짜 부분에 시간을 제거
    df_merged['날짜'] = df_merged['날짜'].dt.date

    # 일일 증가량 계산 (오늘 - 어제)
    # df_merged['확진자'] --> 누적 (날짜별로 계속 증가하는 수치)
    # .diff() --> 차이 (오늘 - 어제)
    # .fillna(0) --> 첫번째날은 비교대상이 없으니 NaN -> 0으로 채운다
    # .astype(int) --> 결과를 정수형으로

    df_merged['신규 확진자'] = df_merged['확진자'].diff().fillna(0).astype(int)
    df_merged['신규 사망자'] = df_merged['사망자'].diff().fillna(0).astype(int)
    df_merged['신규 회복자'] = df_merged['회복자'].diff().fillna(0).astype(int)

    # 탭 3개 구성 (감염 추이, 통계 요약, 비율 분석)
    tab1, tab2, tab3 = st.tabs(['📈 감염 추이', '📊 통계 요약', '⚖️ 비율 분석'])

    # 첫번째 탭 -> 감염 추이
    with tab1:
        st.subheader('📈 누적 추이 그래프')
        selected = st.multiselect('표시할 항목을 선택하세요', ['확진자', '사망자', '회복자'], default=['확진자', '회복자']) # 기본값 -> 확진자, 회복자 그래프 나온다
        if selected: # 선택된 값이 있다면 -> 그래프를 그린다
            fig = px.line(df_merged, x='날짜', y=selected, markers=True)
            st.plotly_chart(fig, use_container_width=True) # 부모 너비 기준

        st.subheader('🆕 일일 증가량 그래프')
        selected_new = st.multiselect('표시할 항목 (신규)를 선택하세요.', ['신규 확진자', '신규 사망자', '신규 회복자'], default=['신규 확진자'])
        if selected_new:
            fig_new = px.bar(df_merged, x='날짜', y=selected_new)
            st.plotly_chart(fig_new, use_container_width=True)

    # 두번째 탭 -> 통계 요약
    with tab2:
        st.subheader('📋 일자별 통계 테이블')
        # .tail(10) --> 끝에서부터 10개
        st.dataframe(df_merged.tail(10), use_container_width=True)

    # 세번째 탭 -> 비율 분석
    with tab3:
        st.subheader('⚖️ 최신일 기준 회복률 / 치명률')
        # 최신날짜가 맨 마지막이니까 -1
        latest = df_merged.iloc[-1]
        # 확진자 -> confirmed
        # 사망자 -> deaths
        # 회복자 -> recovered
        confirmed, deaths, recovered = latest['확진자'], latest['사망자'], latest['회복자']

        # 회복률 = (회복자 / 확진자) * 100
        recovered_rate = (recovered / confirmed) * 100 if confirmed else 0
        # 치명률 = (사망자 / 확진자) * 100
        deaths_rate = (deaths / confirmed) *100 if confirmed else 0

        col1, col2 = st.columns(2) # 열 두개를 만든다
        col1.metric('✅ 회복률', f'{recovered_rate:.2f} %')
        col2.metric('☠️ 치명률', f'{deaths_rate:.2f} %')

        st.subheader('📊 감염자 분포 비율')
        # 원형그래프의 원본이 될 데이터프레임 생성
        pie_df = pd.DataFrame({
            '구분' : ['회복자', '사망자', '격리증'],
            '인원수' : [recovered, deaths, confirmed - recovered - deaths]
        })
        fig_pie = px.pie(pie_df, names='구분', values='인원수', title='감염자 분포')
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info('3개의 CSV 파일 (확진자, 사망자, 회복자)을 모두 업로드해주세요.')