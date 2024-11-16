import streamlit as st
import pandas as pd
import PublicDataReader as pdr
from io import BytesIO

# PublicDataReader의 TransactionPrice 객체를 초기화합니다.
service_key = "S5x2qTobKjleFb37sgF9STDDgi%2FWu4z76rD4OI56d9VTGwENZRUj6NJ3l43DZBDl3vsUb7g%2FQjyw0I%2B19X6k7Q%3D%3D"
api = pdr.TransactionPrice(service_key)

# Streamlit 대시보드의 제목 설정
st.title("아파트 매매 / 전월세 조회")

# Displaying the source attribution
st.markdown('Source: [공공데이터포털](https://www.data.go.kr/)')

# 시군구명 입력 및 시군구 코드 선택을 위한 컬럼 생성
col1, col2 = st.columns(2)

with col1:
    # 사용자 입력을 받는 텍스트 박스 생성
    sigungu_name = st.text_input("시군구명을 입력하세요. 예) 동작구, 강서구 등 ", "강서구")

# 시군구 코드를 가져오는 코드
code = pdr.code_bdong()

# 사용자가 입력한 시군구명에 해당하는 데이터 필터링
filtered_code = code.loc[(code['시군구명'].str.contains(sigungu_name)) & (code['읍면동명'] == '')]

with col2:
    if sigungu_name and not filtered_code.empty:
        # 시군구코드와 시도명을 결합하여 표시할 문자열 생성
        options = filtered_code.apply(lambda row: f"{row['시군구코드']} ({row['시도명']})", axis=1)
        
        # 선택 가능한 시군구 코드와 시도명을 selectbox로 표시
        selected_option = st.selectbox(
            '시군구 코드와 시도명을 선택하세요',
            options
        )
        
        # 선택된 시군구 코드와 시도명을 분리하여 변수 할당
        selected_code, selected_sido_name = selected_option.split(' (')
        selected_sido_name = selected_sido_name.rstrip(')')
    elif sigungu_name:
        st.write("해당 시군구명에 대한 정보를 찾을 수 없습니다.")
    else:
        st.write("시군구명을 입력해주세요.")

# '거래 유형 선택'과 '시작 연월', '종료 연월' 입력을 위한 컬럼 생성
col3, col4, col5 = st.columns([2, 2, 2])

with col3:
    # 거래 유형 선택
    trade_type = st.selectbox(
        "거래유형 선택 (매매 or 전월세)",
        ["매매", "전월세"]
    )

with col4:
    # 시작 연월 입력
    start_year_month = st.text_input("시작 연월 입력 (예: 202401)", "202401")

with col5:
    # 종료 연월 입력
    end_year_month = st.text_input("종료 연월 입력 (예: 2024011)", "202411")

# 선택된 시군구 코드와 사용자가 입력한 기간에 따라 데이터 조회
if 'selected_code' in locals() and start_year_month and end_year_month:
    try:
        df = api.get_data(
            property_type="아파트",
            trade_type=trade_type,  # 사용자가 선택한 거래 유형
            sigungu_code=selected_code,
            start_year_month=start_year_month,
            end_year_month=end_year_month,
        )

        if not df.empty:
            # '아파트'를 메인 필터로 사용하여 필터링 옵션 제공
            apartment_options = st.selectbox("아파트를 선택하세요", df['아파트'].unique())
            filtered_df = df[df['아파트'] == apartment_options]
            
            # 인덱스 1부터 시작하도록 조정
            filtered_df.index = range(1, len(filtered_df) + 1)
            
            # 거래 유형에 따라 다른 컬럼 표시
            if trade_type == "매매":
                columns = ['아파트', '법정동', '도로명', '건축년도', '층', '전용면적', '년', '월', '일', '거래금액', '거래유형']
            else:  # "전월세"
                columns = ['아파트', '법정동', '지번', '건축년도', '층', '전용면적', '년', '월', '일', '보증금액', '월세금액', '계약구분', '계약기간']
                
            # 필터링된 데이터 표시 (인덱스 1부터 시작)
            st.dataframe(filtered_df[columns])

            # Excel 파일로 변환 및 다운로드 버튼 제공
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Excel 내 인덱스 1부터 시작하도록 조정
                filtered_df.index = range(1, len(filtered_df) + 1)
                filtered_df.to_excel(writer, index=True)
            excel_data = output.getvalue()

            if trade_type == "매매":
                file_name = f'아파트_매매_result_{start_year_month}_to_{end_year_month}.xlsx'
            else:  # "전월세"
                file_name = f'아파트_전월세_result_{start_year_month}_to_{end_year_month}.xlsx'

            st.download_button(label="Download Excel",
                            data=excel_data,
                            file_name=file_name,
                            mime='application/vnd.ms-excel')

        else:
            st.write("조회된 거래 정보가 없습니다.")
    except Exception as e:
        st.write("데이터를 조회하는 중 오류가 발생했습니다:", str(e))
else:
    st.write("시군구 코드와 조회 기간을 입력해주세요.")


