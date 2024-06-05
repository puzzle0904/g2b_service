#import debugpy      # 멀티 쓰레드 디버깅을 위해서는 주석제거
## 추가로 필요한 패키지는 BS4, PyQt5, lxml, pandas

import os
import time
import math
import json
import sqlite3      # DBMS 임포트
import pandas
import webbrowser

from urllib import parse, request
from pandas import DataFrame
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from PyQt5.QtCore import *

from WaitingSpinnerWidget import Overlay                # 로딩 스피너
import apikey

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # python실행 경로

## 고정값 설정
DB_FILE = "G2BDB.db"            # DB 파일명 지정
API_KEY = apikey.mykey

API_URL = "http://apis.data.go.kr/1230000/BidPublicInfoService04" # 입찰공고 정보 API
API_URL2 = "http://apis.data.go.kr/1230000/CntrctInfoService" # 계약현황 정보 API

OPT_NAME_BIDT = "/getBidPblancListInfoThngPPSSrch01?" # 입찰공고 물품조회
OPT_NAME_BIDC = "/getBidPblancListInfoCnstwkPPSSrch01?" # 입찰공고 공사조회
OPT_NAME_BIDS = "/getBidPblancListInfoServcPPSSrch01?" # 입찰공고 용역조회
OPT_NAME_BIDF = "/getBidPblancListInfoFrgcptPPSSrch01?" # 입찰공고 외자조회
OPT_NAME_BIDE = "/getBidPblancListInfoEtcPPSSrch01?" # 입찰공고 기타조회

OPT_NAME_CTRT = "/getCntrctInfoListThngPPSSrch?" # 계약현황 물품조회
OPT_NAME_CTRC = "/getCntrctInfoListCnstwkPPSSrch?" # 계약현황 공사조회
OPT_NAME_CTRS = "/getCntrctInfoListServcPPSSrch?" # 계약현황 용역조회
OPT_NAME_CTRF = "/getCntrctInfoListFrgcptPPSSrch?" # 계약현황 외자조회

## 검색중인URL 저장용 전역변수
url_pre = ""
url_sub = ""

## DB파일이 없으면 새로 만들고

if os.path.isfile(BASE_DIR + "//" + DB_FILE):
    con = sqlite3.connect(BASE_DIR + "//" + DB_FILE)
    cursor = con.cursor()
    
else:
    con = sqlite3.connect(BASE_DIR + "//" + DB_FILE)
    cursor = con.cursor()
    cursor.execute("CREATE TABLE bid_list(bidno text PRIMARY KEY, bidissue date, bidname text, client text, price text, url text)")
    cursor.execute("CREATE TABLE bid_saved(bidno text PRIMARY KEY, bidname text)")

Ui_MainWindow = uic.loadUiType(BASE_DIR+r'/G2BDataAPI.ui')[0]
#Ui_MainWindow = uic.loadUiType(r'D:\VSCode\MyPython_collection\G2BDataAPI\G2BDataAPI\G2BDataAPI.ui')[0]

global start_time       #데이터 다운로드 시간 계산용 전역변수
start_time = 0.0

## 데이터 크롤링을 담당할 쓰레드
class CrawlRunnable(QRunnable):
    def __init__(self, dialog):
        QRunnable.__init__(self)
        self.w = dialog

    # 크롤링 루틴
    def crawl(self):        
        #debugpy.debug_this_thread()     # 멀티 쓰레드 디버깅을 위해서 추가
        date_start = self.w.dateEdit_start.date().toString("yyyyMMdd")
        date_end = self.w.dateEdit_end.date().toString("yyyyMMdd")
        page_no = self.w.lineEdit_curPage.text()                            #페이지
        dminsttNm = self.w.lineEdit_dminsttNm.text()                        #수요기관
        presmptPrceBgn = int(self.w.lineEdit_minVal.text())*100000000       #추정가격
        bidNtceNm = self.w.lineEdit.text()                                  #공고명
        
        start = parse.quote(str(date_start))                                #검색기간 시작일
        end = parse.quote(str(date_end))                                    #검색기간 종료일
        keyword = parse.quote(self.w.lineEdit.text())                       #공고명 검색 키워드
        numOfRows = parse.quote(str(27))                                    #페이지당 표시할 공고 수
        page = parse.quote(str(page_no))                                    #다운로드할 페이지 번호

        if self.w.radioButton_bidT.isChecked():                     # "입찰공고 물품 버튼" 선택 시
            url = (API_URL + OPT_NAME_BIDT
               + "numOfRows="+numOfRows+"&"
               + "pageNo="+ page_no+"&"
               + "ServiceKey="+API_KEY+"&"
               + "inqryDiv=1&"
               + "inqryBgnDt="+start+"0000&"
               + "inqryEndDt="+end+"2359"
               )
            
            if bidNtceNm != "":                                     # 공고명
                url = url+"&"+"bidNtceNm="+parse.quote(bidNtceNm)       
            
            if dminsttNm != "":                                     # 수요기관 검색조건이 있으면 추가
                url = url+"&"+"dminsttNm="+parse.quote(dminsttNm)     

            if presmptPrceBgn != 0:
                url = url+"&"+"presmptPrceBgn="+parse.quote(str(presmptPrceBgn))    # 추정가격 검색조건이 있으면 추가
                
            print(url)

            
        
        elif self.w.radioButton_bidC.isChecked():                   # "입찰공고 공사 버튼" 선택 시
            url = (API_URL + OPT_NAME_BIDC
               + "numOfRows="+numOfRows+"&"
               + "pageNo="+page_no+"&"
               + "ServiceKey="+API_KEY+"&"
               + "inqryDiv=1&"
               + "inqryBgnDt="+start+"&"
               + "inqryEndDt="+end
               )
            
            if bidNtceNm != "":                                     # 공고명
                url = url+"&"+"bidNtceNm="+parse.quote(bidNtceNm)       
            
            if dminsttNm != "":                                     # 수요기관 검색조건이 있으면 추가
                url = url+"&"+"dminsttNm="+parse.quote(dminsttNm)     

            if presmptPrceBgn != 0:
                url = url+"&"+"presmptPrceBgn="+parse.quote(str(presmptPrceBgn))    # 추정가격 검색조건이 있으면 추가

        elif self.w.radioButton_bidS.isChecked():                   # "입찰공고 용역 버튼" 선택 시
            url = (API_URL + OPT_NAME_BIDS
               + "numOfRows="+numOfRows+"&"
               + "pageNo="+page_no+"&"
               + "ServiceKey="+API_KEY+"&"
               + "inqryDiv=1&"
               + "inqryBgnDt="+start+"&"
               + "inqryEndDt="+end
               )
            
            if bidNtceNm != "":                                     # 공고명
                url = url+"&"+"bidNtceNm="+parse.quote(bidNtceNm)       
            
            if dminsttNm != "":                                     # 수요기관 검색조건이 있으면 추가
                url = url+"&"+"dminsttNm="+parse.quote(dminsttNm)     

            if presmptPrceBgn != 0:
                url = url+"&"+"presmptPrceBgn="+parse.quote(str(presmptPrceBgn))    # 추정가격 검색조건이 있으면 추가

        elif self.w.radioButton_bidF.isChecked():                   # "입찰공고 외자 버튼" 선택 시
            url = (API_URL + OPT_NAME_BIDF
               + "numOfRows="+numOfRows+"&"
               + "pageNo="+page_no+"&"
               + "ServiceKey="+API_KEY+"&"
               + "inqryDiv=1&"
               + "inqryBgnDt="+start+"&"
               + "inqryEndDt="+end
               )
            
            if bidNtceNm != "":                                     # 공고명
                url = url+"&"+"bidNtceNm="+parse.quote(bidNtceNm)       
            
            if dminsttNm != "":                                     # 수요기관 검색조건이 있으면 추가
                url = url+"&"+"dminsttNm="+parse.quote(dminsttNm)     

            if presmptPrceBgn != 0:
                url = url+"&"+"presmptPrceBgn="+parse.quote(str(presmptPrceBgn))    # 추정가격 검색조건이 있으면 추가
                
        elif self.w.radioButton_bidE.isChecked():                   # "입찰공고 기타 버튼" 선택 시
            url = (API_URL + OPT_NAME_BIDE
               + "numOfRows="+numOfRows+"&"
               + "pageNo="+page_no+"&"
               + "ServiceKey="+API_KEY+"&"
               + "inqryDiv=1&"
               + "inqryBgnDt="+start+"&"
               + "inqryEndDt="+end
               )
            
            if bidNtceNm != "":                                     # 공고명
                url = url+"&"+"bidNtceNm="+parse.quote(bidNtceNm)       
            
            if dminsttNm != "":                                     # 수요기관 검색조건이 있으면 추가
                url = url+"&"+"dminsttNm="+parse.quote(dminsttNm)     

            if presmptPrceBgn != 0:
                url = url+"&"+"presmptPrceBgn="+parse.quote(str(presmptPrceBgn))    # 추정가격 검색조건이 있으면 추가
                
        else :
            print("에러")

        req = request.Request(url)
        resp = request.urlopen(req)

        rescode = resp.getcode()
        if(rescode==200):
            response_body = resp.read()
            html=response_body.decode('utf-8')
            soup = BeautifulSoup(html, 'lxml')

            errmsg = soup.find('errmsg')
            if(errmsg!=None):
                return 0

            ## BeautifulSoup에서 아이템 검색시 모두 소문자로 검색해야 함
            totalCount = soup.find('totalcount')    #검색조건에 해당하는 전체 공고수
            pageNo = soup.find('pageno')            #요청한 페이지 번호
            totalPageNo = math.ceil(int(totalCount.string) / int(numOfRows))    #전체 페이지 수

            self.w.label_3.setText(str(totalPageNo)+"페이지("+totalCount.string+"건)중 페이지")
            self.w.lineEdit_curPage.setText(pageNo.string)

            ## 크롤링 쓰레드에서 처리할 DB연결
            con = sqlite3.connect(BASE_DIR + "//" + DB_FILE)
            cursor = con.cursor()

            for itemElement in soup.find_all('item'):
                #조회 데이터를 DB에 입력
                if self.w.radioButton_bidT.isChecked():
                    price = itemElement.presmptprce.string
                    if price == None:
                        price = "0"
                    price = format(int(price),',')
                    cursor.execute("INSERT or IGNORE INTO bid_list VALUES(?,?,?,?,?,?);",
                                  (itemElement.bidntceno.string,            # 공고번호
                                  itemElement.bidntcedt.string,             # 공고일시
                                  itemElement.bidntcenm.string,             # 공고명
                                  itemElement.dminsttnm.string,             # 발주처
                                  price,                                    # 가격
                                  itemElement.bidntcedtlurl.string))        # 공고문주소

                elif self.w.radioButton_ctrC.isChecked():
                    price = itemElement.thtmcntrctamt.string
                    if price == None:
                        price = "0"
                    price = format(int(price),',')
                    cursor.execute("INSERT or IGNORE INTO bid_list VALUES(?,?,?,?,?,?);",
                                  (itemElement.untycntrctno.string,         # 계약번호
                                  itemElement.cntrctcnclsdate.string,       # 계약체결일
                                  itemElement.cnstwknm.string,              # 공사명
                                  itemElement.cntrctinsttnm.string,         # 계약기관
                                  price,         # 금회계약금액
                                  itemElement.cntrctdtlinfourl.string))     # 공고문주소

                elif self.w.radioButton_bidE.isChecked():
                    price = itemElement.presmptprce.string
                    if price == None:
                        price = "0"
                    price = format(int(price),',')
                    cursor.execute("INSERT or IGNORE INTO bid_list VALUES(?,?,?,?,?,?);",
                                  (itemElement.bidntceno.string,            # 공고번호
                                  itemElement.bidntcedt.string,             # 공고일시
                                  itemElement.bidntcenm.string,             # 공고명
                                  itemElement.dminsttnm.string,             # 발주처
                                  price,                                    # 가격
                                  itemElement.bidntcedtlurl.string))        # 공고문주소

                else:
                    price = itemElement.thtmcntrctamt.string
                    if price == None:
                        price = "0"
                    price = format(int(price),',')
                    cursor.execute("INSERT or IGNORE INTO bid_list VALUES(?,?,?,?,?,?);",
                                  (itemElement.untycntrctno.string,         # 계약번호
                                  itemElement.cntrctcnclsdate.string,       # 계약체결일
                                  itemElement.cntrctnm.string,              # 계약명
                                  itemElement.cntrctinsttnm.string,         # 계약기관
                                  price,         # 금회계약금액
                                  itemElement.cntrctdtlinfourl.string))     # 공고문주소

                con.commit()    # 작업내용을 테이블에 수행
            con.close()
    
        else:
            print("Error Code:" + rescode)

    def run(self):
        self.crawl()
        QMetaObject.invokeMethod(self.w, "search_finish",
                                 Qt.QueuedConnection)

class MyDialog(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initMainTable()

        self.overlay = Overlay(self.centralWidget())
        self.overlay.hide()
  
        self.pushButton.clicked.connect(self.btn_search)
        self.pushButton_move.clicked.connect(self.btn_move)
        self.pushButton_del.clicked.connect(self.btn_del)

        self.pushButton_today.clicked.connect(self.btn_today)
        self.pushButton_3days.clicked.connect(self.btn_3days)
        self.pushButton_1week.clicked.connect(self.btn_1week)
        self.pushButton_1month.clicked.connect(self.btn_1month)
        self.pushButton_3months.clicked.connect(self.btn_3months)

        self.radioButton_bidT.clicked.connect(self.radioB_bidT)
        self.radioButton_bidC.clicked.connect(self.radioB_bidC)
        self.radioButton_bidS.clicked.connect(self.radioB_bidS)
        self.radioButton_bidF.clicked.connect(self.radioB_bidF)
        self.radioButton_bidE.clicked.connect(self.radioB_bidE)

        self.radioButton_ctrT.clicked.connect(self.radioB_ctrT)
        self.radioButton_ctrC.clicked.connect(self.radioB_ctrC)
        self.radioButton_ctrS.clicked.connect(self.radioB_ctrS)
        self.radioButton_ctrF.clicked.connect(self.radioB_ctrF)

        self.tableWidget.cellClicked.connect(self.cell_clicked)
        self.tableWidget.cellDoubleClicked.connect(self.cell_DBclicked)

        self.dateEdit_start.setDate(QDate.currentDate())
        self.dateEdit_end.setDate(QDate.currentDate())

    # Pyqt종료시 호출
    def closeEvent(self, event):
        con.close()     # DB연결 종료
        super(MyDialog, self).closeEvent(event)

    # Resize 이벤트
    def resizeEvent(self, event):
        super(MyDialog, self).resizeEvent(event)
        self.arrangecolumn()
        self.overlay.resize(event.size())

    def showEvent(self, a0):
        self.arrangecolumn()
        return super().showEvent(a0)

    # 메인테이블에 DB 데이터 표시하기
    def refreshMainTable(self):
        con = sqlite3.connect(BASE_DIR + "//" + DB_FILE)
        cursor = con.cursor()
        cursor.execute("SELECT * FROM bid_list")
        table = self.tableWidget
        table.setRowCount(0)
        for row, form in enumerate(cursor):
            table.insertRow(row)
            for column, item in enumerate(form):
                if (column<5):
                    table.setItem(row, column, QTableWidgetItem(str(item)))
        self.arrangecolumn()
        con.close()  
        
    # 메인테이블 초기화
    def initMainTable(self):
        table = self.tableWidget

        table.setColumnCount(5)
        table.setRowCount(0)
        table.setHorizontalHeaderLabels(["번호","공고/계약일","사업명","기관명","금액"])

        self.refreshMainTable()

    # 테이블 삭제
    def btn_del(self):
        con = sqlite3.connect(BASE_DIR + "//" + DB_FILE)
        cursor = con.cursor()
        cursor.execute("DELETE FROM bid_list;")
        con.commit()    # 작업내용을 테이블에 수행
        con.close()
        self.refreshMainTable()

    # 입찰공고를 검색하기
    def btn_search(self):
        global start_time
        start_time = time.time()            # 시작시간 리셋
        self.overlay.setVisible(True)       # 스피너 시작

        ## 검색페이지 요청
        table = self.tableWidget
        table.clearContents()

        runnable = CrawlRunnable(self)
        QThreadPool.globalInstance().start(runnable)

    # 페이지 이동
    def btn_move(self):
        self.btn_del()
        self.btn_search()

    # 키워드목록에서 클릭이 발생하면 해당 키워드 열 선택
    def cell_clicked(self, row, col):
        selection_range = QTableWidgetSelectionRange(row, 0, row, self.tableWidget.columnCount() - 1)
        self.tableWidget.setRangeSelected(selection_range, True)


    # 키워드목록에서 더블클릭이 발생하면 해당 항목의 공고문을 웹브라우저로 호출
    def cell_DBclicked(self, row, col):
        sel_key = self.tableWidget.item(row, 2)
        if sel_key is not None:
            sel_key = sel_key.text()
            QMessageBox.information(self, "선택한 키", sel_key)
        else:
            QMessageBox.warning(self, "경고", "데이터가 없습니다.")

    # 검색조건 프리셋


    ## 업무구분

    def radioB_bidT(self):
        self.radioButton_bidT.setChecked(True)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)
    
    def radioB_bidC(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(True)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_bidS(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(True)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_bidF(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(True)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_bidE(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(True)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_ctrT(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(True)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_ctrC(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(True)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(False)

    def radioB_ctrS(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(True)
        self.radioButton_ctrF.setChecked(False)

    def radioB_ctrF(self):
        self.radioButton_bidT.setChecked(False)
        self.radioButton_bidC.setChecked(False)
        self.radioButton_bidS.setChecked(False)
        self.radioButton_bidF.setChecked(False)
        self.radioButton_bidE.setChecked(False)
        self.radioButton_ctrT.setChecked(False)
        self.radioButton_ctrC.setChecked(False)
        self.radioButton_ctrS.setChecked(False)
        self.radioButton_ctrF.setChecked(True)

    ## 검색기간
    def btn_today(self):
        self.dateEdit_start.setDate(QDate.currentDate())
        self.dateEdit_end.setDate(QDate.currentDate())

    def btn_3days(self):
        self.dateEdit_start.setDate(QDate.currentDate().addDays(-2))
        self.dateEdit_end.setDate(QDate.currentDate())

    def btn_1week(self):
        self.dateEdit_start.setDate(QDate.currentDate().addDays(-7))
        self.dateEdit_end.setDate(QDate.currentDate())

    def btn_1month(self):
        self.dateEdit_start.setDate(QDate.currentDate().addMonths(-1))
        self.dateEdit_end.setDate(QDate.currentDate())

    def btn_3months(self):
        self.dateEdit_start.setDate(QDate.currentDate().addMonths(-2))
        self.dateEdit_end.setDate(QDate.currentDate())

    def arrangecolumn(self):
        table = self.tableWidget
        header = table.horizontalHeader()
        twidth = header.width()
        width = []
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
            width.append(header.sectionSize(column))

        wfactor = twidth / sum(width)
        for column in range(header.count()):
            header.setSectionResizeMode(column, QHeaderView.Interactive)
            
            header.resizeSection(column, int(width[column]*wfactor))

    @pyqtSlot()
    def search_finish(self):
        self.refreshMainTable()
        self.overlay.setVisible(False)
        
        ## 실행시간 표시
        global start_time
        end_time = time.time() ##계산완료시간
        time_consume = end_time - start_time
        time_consume = '%0.2f' % time_consume  ##소수점2째자리이하는 버림
        self.lineEdit_time.setText(str(time_consume) + "초 소요")
             
if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    dial = MyDialog()
    dial.show()           
    sys.exit(app.exec_())
    
