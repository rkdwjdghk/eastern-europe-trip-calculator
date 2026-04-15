import streamlit as st
import re
import streamlit.components.v1 as components
import html

st.set_page_config(page_title="유럽상품1팀 인솔자 출장비 계산기", layout="centered")

st.title("유럽상품1팀 인솔자 출장비 계산기")
st.caption("ver 1.0.0.1")
st.divider()

# 세션 상태 초기화
if "show_note_form" not in st.session_state:
    st.session_state.show_note_form = False
if "calculation_done" not in st.session_state:
    st.session_state.calculation_done = False
if "result_formula" not in st.session_state:
    st.session_state.result_formula = ""
if "result_type" not in st.session_state:
    st.session_state.result_type = ""
if "result_message" not in st.session_state:
    st.session_state.result_message = ""
if "sub_message" not in st.session_state:
    st.session_state.sub_message = ""
if "generated_note_text" not in st.session_state:
    st.session_state.generated_note_text = ""

# 상품코드 입력
product_code_input = st.text_input("상품코드 입력", max_chars=15)
product_code = product_code_input.upper()

if product_code_input and product_code_input != product_code:
    st.caption(f"자동 대문자 변환: {product_code}")

# 코드 분류
code_prefix_6 = product_code[:6] if len(product_code) >= 6 else ""

special_balkan_prefixes = ["EEP130", "EEP137", "EEP139", "EEP145"]
special_spain_prefixes = ["EEP131", "EEP117"]

is_special_balkan_code = code_prefix_6 in special_balkan_prefixes
is_special_spain_code = code_prefix_6 in special_spain_prefixes

# 상품 날짜 수 입력
travel_days = st.number_input("상품 날짜 수 입력", min_value=1, value=9, step=1)

# 인원 수 입력
people_count = st.number_input("인솔자 제외 인원수", min_value=1, step=1)

# 식사 불포함 횟수
meal_excluded_count = st.number_input("식사 불포함 횟수 입력", min_value=0, step=1)

# 체크박스 순서
prague_night_tour = st.checkbox("프라하 야간투어 스페셜 포함 상품인가요?")
vienna_special = st.checkbox("비엔나 음악회 스페셜 포함 상품인가요?")
return_after_20 = st.checkbox("귀국편 출발 시간이 20시 이후인가요?")
departure_before_559 = st.checkbox("출발편 시간이 오전 05:59 이전인가요?")
star_guide = st.checkbox("스타 인솔자 상품인가요?")
balkan_visit = st.checkbox("발칸 방문 여부")

# 발칸 방식 적용 여부
# 스페인일주 코드는 발칸보다 우선
is_balkan_style = (balkan_visit or is_special_balkan_code) and not is_special_spain_code

# 발칸 방식일 때만 발칸 방문 일수 표시
balkan_days = 0
if is_balkan_style:
    balkan_days = st.number_input("발칸 방문 일수 입력", min_value=1, step=1)

def is_valid_product_code(code):
    pattern = r'^[A-Z]{3}\d{9}.{3}$'
    return bool(re.match(pattern, code))

def get_product_grade(code):
    fifth_char = code[4]
    if fifth_char in ["3", "4"]:
        return "스탠다드"
    elif fifth_char == "1":
        return "프리미엄"
    elif fifth_char == "6":
        return "세이브"
    else:
        return "등급 판별 불가"

if st.button("계산하기"):
    st.session_state.show_note_form = False
    st.session_state.calculation_done = False
    st.session_state.result_formula = ""
    st.session_state.result_message = ""
    st.session_state.result_type = ""
    st.session_state.sub_message = ""
    st.session_state.generated_note_text = ""

    errors = []

    if len(product_code) != 15:
        errors.append("상품코드는 총 15자리여야 합니다.")
    elif not is_valid_product_code(product_code):
        errors.append("상품코드 형식이 올바르지 않습니다.")

    if travel_days <= 0:
        errors.append("상품 날짜 수는 1일 이상이어야 합니다.")

    if people_count <= 0:
        errors.append("인솔자 제외 인원수는 1명 이상이어야 합니다.")

    if is_balkan_style and balkan_days <= 0:
        errors.append("발칸 방식 상품의 경우, 발칸 방문 일수를 입력해야 합니다.")

    if is_balkan_style and travel_days == 12 and balkan_days > 12:
        errors.append("12일 발칸 방식 상품의 발칸 방문 일수는 12일을 초과할 수 없습니다.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        grade = get_product_grade(product_code)
        st.session_state.calculation_done = True

        if grade == "세이브":
            st.session_state.result_message = "아직 개발중입니다😟"
            st.session_state.result_type = "warning"

        elif grade in ["스탠다드", "프리미엄"]:
            applied_people_count = people_count if people_count >= 15 else 15
            formula_parts = []
            extra_amount = 0
            messages = []

            # 1. 스페인일주 방식
            if is_special_spain_code:
                if grade == "스탠다드":
                    if applied_people_count <= 19:
                        base_amount = 150000 * travel_days
                        formula_parts.append(f"(150,000원 * {travel_days}일)")
                    elif 20 <= applied_people_count <= 24:
                        base_amount = 200000 * travel_days
                        formula_parts.append(f"(200,000원 * {travel_days}일)")
                    else:
                        base_amount = (200000 * travel_days) + 300000
                        formula_parts.append(f"(200,000원 * {travel_days}일)")
                        formula_parts.append("(25명 이상 추가 300,000원)")
                else:  # 프리미엄
                    base_amount = 200000 * travel_days
                    formula_parts.append(f"(200,000원 * {travel_days}일)")

                messages.append(f"상품코드 {code_prefix_6}는 스페인일주 방식으로 자동 적용되었습니다.")

            # 2. 발칸 방식
            elif is_balkan_style:
                if travel_days == 12:
                    normal_days = 12 - balkan_days
                    balkan_special_days = balkan_days

                    first_part = 12000 * applied_people_count * normal_days
                    second_part = 16000 * applied_people_count * balkan_special_days
                    base_amount = first_part + second_part

                    formula_parts.append(f"(12,000원 * {applied_people_count}명 * {normal_days}일)")
                    formula_parts.append(f"(16,000원 * {applied_people_count}명 * {balkan_special_days}일)")
                else:
                    first_part = 12000 * applied_people_count * 2
                    second_part = 16000 * applied_people_count * (travel_days - 2)
                    base_amount = first_part + second_part

                    formula_parts.append(f"(12,000원 * {applied_people_count}명 * 2일)")
                    formula_parts.append(f"(16,000원 * {applied_people_count}명 * {travel_days - 2}일)")

                if is_special_balkan_code:
                    messages.append(f"상품코드 {code_prefix_6}는 발칸 방식으로 자동 적용되었습니다.")

                if grade == "프리미엄":
                    extra_amount += 200000
                    formula_parts.append("(프리미엄 200,000원)")

            # 3. 일반 방식
            else:
                if applied_people_count >= 20:
                    price_per_person_per_day = 12000
                else:
                    price_per_person_per_day = 13000

                base_amount = applied_people_count * price_per_person_per_day * travel_days
                formula_parts.append(f"{travel_days}일 * {applied_people_count}명 * {price_per_person_per_day:,}원")

                if grade == "프리미엄":
                    extra_amount += 200000
                    formula_parts.append("(프리미엄 200,000원)")

            # 추가 금액
            if meal_excluded_count > 0:
                meal_extra = meal_excluded_count * 30000
                extra_amount += meal_extra
                formula_parts.append(f"(식사불포함 {meal_excluded_count}회 {meal_extra:,}원)")

            if prague_night_tour:
                extra_amount += 70000
                formula_parts.append("(프라하야간투어 70,000원)")

            if vienna_special:
                extra_amount += 70000
                formula_parts.append("(비엔나음악회 70,000원)")

            if departure_before_559:
                extra_amount += 50000
                formula_parts.append("(출발편 05:59 이전 50,000원)")

            if return_after_20:
                extra_amount += 30000
                formula_parts.append("(귀국편 20시 이후 30,000원)")

            if star_guide:
                extra_amount += 300000
                formula_parts.append("(스타 인솔자 300,000원)")

            total_amount = base_amount + extra_amount
            formula = " + ".join(formula_parts) + f" = {total_amount:,}원"

            if people_count <= 14:
                messages.insert(0, f"입력 인원 {people_count}명은 최소 기준에 따라 15명으로 소급 적용되었습니다.")

            st.session_state.sub_message = "\n".join(messages)
            st.session_state.result_formula = formula
            st.session_state.result_message = f"출장비 계산 : {formula}"
            st.session_state.result_type = "success"

        else:
            st.session_state.result_message = "상품코드 5번째 자리로 등급을 판별할 수 없습니다."
            st.session_state.result_type = "error"

# 계산 결과 표시
if st.session_state.calculation_done:
    st.subheader("계산 결과")

    if st.session_state.sub_message:
        st.info(st.session_state.sub_message)

    if st.session_state.result_type == "success":
        st.success(st.session_state.result_message)
    elif st.session_state.result_type == "warning":
        st.warning(st.session_state.result_message)
    elif st.session_state.result_type == "error":
        st.error(st.session_state.result_message)

    if st.session_state.result_type == "success":
        if st.button("인솔자 쪽지 양식 작성"):
            st.session_state.show_note_form = True

# 쪽지 양식 입력 영역
if st.session_state.show_note_form:
    st.subheader("인솔자 쪽지 양식 작성")
    manager_name = st.text_input("상품 담당자 이름")
    visit_czech = st.checkbox("체코를 방문하는 상품인가요?")
    visit_hallstatt = st.checkbox("할슈타트를 방문하는 상품인가요?")

    if st.button("실행"):
        czech_text = ""
        if visit_czech:
            czech_text = f"""
*{product_code} 영문여행자보험증서

- 영문여행자 보험 증서 : 체코에서 여행자와 불법이민자 구분을 여행자보험 증서로 확인한다고 합니다.
고객님들께 한부씩 전달 부탁드립니다. 현재 보험 시스템상 다른고객님들은 상관없는데 인솔자 등록 시스템 연동이 안돼서 인솔자님 성이 빠진 채 나옵니다.
영문 보험증서만 성이 빠진 채 나오는 것이며, 국문은 정상으로 나오기 때문에 보험엔 문제 없음을 확인했습니다.
"""

        hallstatt_text = ""
        if visit_hallstatt:
            hallstatt_text = """

6) 할슈타트 내 행사 진행 시에는 멘트는 꼭 버스 안에서만 진행해 주시고, 야외에서는 자유 일정으로 진행 부탁드립니다. 야외에서의 가이드 행위가 엄격히 금지되어 있는 지역으로, 가이드 분들이 현지 경찰에 인계되는 사례가 종종 발생하고 있습니다.
"""

        note_text = f"""인솔자님 안녕하세요, 하나투어 유럽상품1팀 {manager_name}입니다 :)



{product_code} 상품 행사 관련 서류 전달드립니다.



FNL 확정서 식당까지 모두 확정되어, 확정일정표 반영해두었습니다. 한글일정표 인쇄 이상없습니다.



감사합니다.

===============================================================

<행사 특이사항>



- 선택관광 선포함자는 총 n명입니다. 

nnn, nnn 님.



- 현지서비스 :  

nnn 님 초콜릿 1개 <멘트 : >


총 : 초콜릿 1개



- 기타 특이사항 :





===============================================================

{czech_text}
* 출장비 관련 내용
출장비는 인솔자님 계좌로 내일 모레 목요일 송금 예정입니다.(세금 3.3% 제외)

{st.session_state.result_formula}

================================================================================
그 외 공통안내 서류 > (면책동의서,일정변경동의서,안전사고매뉴얼,비상상황 대응매뉴얼 등)
링크로 들어가서 다운로드 가능합니다. 출발 전 꼭 체크 부탁드립니다.
https://drive.google.com/drive/folders/1Tf_4RBZMWziPzlJBWKOim4HfNWok-4L6?usp=sharing



중요> 하나투어 여행 개런티 프로그램
 - 일정에 없는 쇼핑, 선택관광, 가이드/기사 경비 지불시 100% 전액환불입니다.
   => 개런티 프로그램 숙지하셔서 일정표에 없는 쇼핑,선택관광,팁 요구 등이 발생하지 않도록 해주세요
 - 일정 변경 사항이 있을 경우 반드시 일정변경동의서를 받아야 합니다. 
 페이지 자세히보기: https://www.hanatour.com/mkt/fet/PL00113329?dtcmProdAttrDvCd=P&oppbTitlNm=하나투어 개런티 프로그램&plnnExhtId=PL00113329&plnnExhtDesc=



출발 전 변경 사항 및 궁금하신 상황은 문의 부탁드립니다.

* 일정표에 있는 자유시간은 웬만하면 꼭 지켜주세요 (차이가 나도 10~ 20분 선에서 진행되게끔)
  - 피치 못할 사정으로 자유시간이 줄어들면 손님들께 설명을 잘 부탁드립니다.

================================================================================

<행사시 유의사항>

1) 수신기 관련 : 전날에 문자로 수령안내 온다고 합니다. 
수신기 분실시 1개당 100유로 발생되오니 손님께 안내 부탁드립니다. 분실 비용은 손님께 현장에서 받아서 귀국 후 수신기 반납시 비용 주시는걸로 해주세요.

2) 손님분들 꼭 여권 및 영문보험증서 지참해주세요

3) 물값관련
- 하나투어는 물값, 매너팁 등의 명목으로 고객에게 공동경비외에 추가로 경비를 받지 않습니다
- 타 지역 스페인 현지에서 협조요청사항이 한가지 있어서 이렇게 게시판에 공지올려드리니, 참고 부탁드리며, 이러한 일이 발생되지않도록 주의해주시기 바랍니다. 현재 스페인지역에서 중국식당, 일부 현지식당을 제외하고, 식사시 물값이 지불되고 있습니다. 최근 물값비용을 절약하기를 위해, 일부 인솔자님들께서 생수를 마트에서 미리 사두셨다가 식당에 들고 들어가서 세팅하는 사례가 빈번해지고 있다고 하며, 이 부분 때문에 코로나 이전에 식당과 로컬사무실의관계 및 업무적인 마찰을 초래했었습니다. 고객님들이 개인적으로 버스나, 가게에서 구입하신 생수를 소지하고 가실 수 는 있으나, 인솔자님들이 고의적으로 구입 후 셋팅하는건 상도에 어긋난다고 판단되며, 이로 인하여, 현장에서 식당 측에서 고객님들께 항의하며, 또 다른 불만을 초래할수 있는 상황이 발생되오니 꼭 주의 부탁드립니다.

4) 호텔객실키 추가반출 금지!!
현지에서 도둑이 카운터에서 호텔 객실키를 발급 받아서 객실내로 침입한 사례가 있었습니다.
카운터네 체크인시 절대 키 추가 반출 되지 않도록 주의주시길 부탁드립니다!
손님들께는 번거로우시겠지만 키는 개별적으로 추가 생성은 불가한 점 안내 부탁드립니다.

5)일정표에 없는 쇼핑이나, 옵션은 진행불가이며 하나투어 일정표와 현지 확정서가 다른지 꼭 확인 부탁드립니다. 
작은 실수가 큰 손해로 이어지지 않도록, 확정표 상 이상하다고 생각되시는 부분 있으시면 꼭 말씀 부탁드리겠습니다.{hallstatt_text}

항상 현장에서 고군분투해주시는 인솔자님께 감사드립니다.

이번 팀도 행사 잘 진행 부탁드리겠습니다!
"""
        st.session_state.generated_note_text = note_text
        st.success("인솔자 쪽지 양식이 생성되었습니다.")

# 생성된 쪽지 표시 + 복사 버튼
if st.session_state.generated_note_text:
    st.subheader("생성된 인솔자 쪽지 전문")

    escaped_text = html.escape(st.session_state.generated_note_text)

    components.html(
        f"""
        <div style="margin-bottom: 12px;">
            <button onclick="copyNoteText()" style="
                background-color:#ff4b4b;
                color:white;
                border:none;
                padding:10px 16px;
                border-radius:8px;
                cursor:pointer;
                font-size:14px;
                font-weight:600;
            ">복사하기</button>
            <span id="copyMessage" style="
                display:none;
                margin-left:12px;
                color:#2e7d32;
                font-weight:600;
            ">인솔자 쪽지 복사가 완료되었습니다!</span>
        </div>

        <textarea id="noteText" readonly style="width:100%; height:700px; padding:12px; font-size:14px;">{escaped_text}</textarea>

        <script>
        function copyNoteText() {{
            const textArea = document.getElementById("noteText");
            textArea.select();
            textArea.setSelectionRange(0, 999999);

            navigator.clipboard.writeText(textArea.value).then(function() {{
                const msg = document.getElementById("copyMessage");
                msg.style.display = "inline";
                setTimeout(function() {{
                    msg.style.display = "none";
                }}, 2000);
            }});
        }}
        </script>
        """,
        height=760,
    )
