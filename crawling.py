import requests
from bs4 import BeautifulSoup
import pandas as pd

def crawl_web_page(sel_key):
    url = sel_key
    response = requests.get(url)
    response.encoding = 'euc-kr'  # 한글 깨짐 방지를 위해 인코딩 설정
    if response.status_code == 200:
        html = response.text
        # 여기서부터 HTML 파싱 및 원하는 정보 추출 작업을 수행합니다.
        soup = BeautifulSoup(html, 'html.parser')

        # 모든 테이블 추출
        tables = soup.find_all('table')

        # 데이터를 담을 딕셔너리 초기화
        data_dict = {}

        # 각 테이블에 대해 반복
        for table in tables:
            # 테이블 내 모든 행(tr) 추출
            rows = table.find_all('tr')
            
            # 각 행에서 데이터 추출
            for row in rows:
                # 행의 모든 셀(th, td) 추출
                cells = row.find_all(['th', 'td'])
                
                # 셀 데이터를 딕셔너리로 저장
                for i in range(0, len(cells), 2):
                    if i + 1 < len(cells):
                        key = cells[i].get_text(strip=True)
                        value = cells[i+1].get_text(strip=True) or "-"
                        if key in data_dict:
                            data_dict[key].append(value)
                        else:
                            data_dict[key] = [value]

        # 데이터프레임으로 변환
        df = pd.DataFrame(data_dict)

        # 숫자형 데이터 변환 및 1000단위 쉼표 추가
        numeric_cols = ['배정예산', '추정가격']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')

        # 필요한 데이터를 추출
        notice_name = df['공고명'].iloc[0] if '공고명' in df.columns else "공고명 없음"
        bid_number = df['입찰공고번호 - 차수'].iloc[0] if '입찰공고번호 - 차수' in df.columns else "-"
        notice_date = df['공고일시'].iloc[0] if '공고일시' in df.columns else "-"
        bid_start = df['입찰서접수 개시일시'].iloc[0] if '입찰서접수 개시일시' in df.columns else "-"
        bid_end = df['입찰서접수 마감일시'].iloc[0] if '입찰서접수 마감일시' in df.columns else "-"
        opening_date = df['개찰일시'].iloc[0] if '개찰일시' in df.columns else "-"
        budget = df['배정예산'].iloc[0] if '배정예산' in df.columns else 0
        estimated_price = df['추정가격'].iloc[0] if '추정가격' in df.columns else 0
        budget_1_percent = budget * 0.87
        budget_0_5_percent = budget * 0.875
        budget_standard = budget * 0.88
        budget_0_5_percent_plus = budget * 0.885
        budget_1_percent_plus = budget * 0.89
        budget_2_percent_plus = budget * 0.90

        # 문자열 포맷팅
        output_text = (
            f"{notice_name}\n"
            f"입찰공고번호-차수: {bid_number}\n"
            f"공고일시: {notice_date}\n"
            f"입찰서접수 개시일시: {bid_start}\n"
            f"입찰서접수 마감일시: {bid_end}\n"
            f"개찰일시: {opening_date}\n"
            "-------------------------------------\n"
            f"배정예산: {budget:,.0f}원 / 추정가격: {estimated_price:,.0f}원\n"
            "\n"
            f"-1%(87%): {budget_1_percent:,.0f}원\n"
            f"-0.5%(87.5%): {budget_0_5_percent:,.0f}원\n"
            f"기준(88%): {budget_standard:,.0f}원\n"
            f"0.5%(88.5%): {budget_0_5_percent_plus:,.0f}원\n"
            f"+1%(89%): {budget_1_percent_plus:,.0f}원\n"
            f"+2%(90%): {budget_2_percent_plus:,.0f}원\n"
        )

        # 데이터를 send.txt 파일에 저장
        with open('/Users/Administrator/Desktop/2024.06.07/g2b_service/send.txt', 'w', encoding='utf-8') as file:
            file.write(output_text)

        print("필요한 정보가 send.txt 파일에 성공적으로 저장되었습니다.")

        # 데이터를 CSV 파일로 저장
        df.to_csv('/Users/Administrator/Desktop/2024.06.07/g2b_service/data.csv', index=False, encoding='utf-8')

        print("CSV 파일이 성공적으로 저장되었습니다.")

        # 추출한 정보를 필요한 형태로 가공하여 반환합니다.
        return soup
    else:
        print("웹페이지를 가져오는 데 실패했습니다.")
        return None
