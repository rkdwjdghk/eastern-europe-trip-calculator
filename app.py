import streamlit as st
import streamlit.components.v1 as components
import html
import json


st.set_page_config(
    page_title="유럽상품1팀 인솔자 출장비 계산기",
    page_icon="💸",
    layout="centered"
)


# -----------------------------
# 상단 헤더
# -----------------------------
st.markdown(
    """
    <div style="margin-top: 0px; margin-bottom: 28px;">
        <h1 style="
            font-size: 42px;
            font-weight: 800;
            color: #1f2937;
            margin-bottom: 18px;
            line-height: 1.2;
        ">
            유럽상품1팀 인솔자 출장비 계산기
        </h1>
        <div style="
            font-size: 13px;
            color: #8a8f98;
            margin-bottom: 52px;
        ">
            ver 1.1.0.1
        </div>
        <hr style="
            border: none;
            border-top: 1px solid #d1d5db;
            margin-bottom: 32px;
        ">
    </div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# 기본 함수
# -----------------------------
def format_won(amount):
    return f"{amount:,}원"


def get_char(text, index):
    """
    index는 0부터 시작합니다.
    상품코드 길이가 부족하면 빈 문자열을 반환합니다.
    """
    if text and len(text) > index:
        return text[index]
    return ""


def is_incentive(product_code):
    """
    상품코드 세 번째 글자가 Q이면 인센티브 방식입니다.
    """
    return get_char(product_code, 2).upper() == "Q"


def is_spain(product_code):
    """
    상품코드 앞 6자리가 EEP131 또는 EEP117이면 스페인일주 방식입니다.
    """
    prefix = product_code[:6].upper() if product_code else ""
    return prefix in ["EEP131", "EEP117"]


def is_premium(product_code):
    """
    상품코드 다섯 번째 글자가 1이면 프리미엄입니다.
    """
    return get_char(product_code, 4) == "1"


def get_applied_people(people):
    """
    인솔자 제외 인원수가 15명 이하이면 15명으로 적용합니다.
    16명 이상이면 입력값 그대로 적용합니다.
    """
    if people <= 15:
        return 15

    return people


def build_people_adjustment_text(original_people, applied_people):
    """
    인원 보정 안내 문구를 생성합니다.
    """
    if original_people != applied_people:
        return f"{original_people}명은 {applied_people}명으로 변경하여 적용했습니다."

    return ""


def get_method_color(method):
    """
    계산 방식별 색상입니다.
    """
    colors = {
        "일반": "#111111",
        "인센티브": "#E53935",
        "스페인일주": "#1E88E5",
        "발칸": "#43A047"
    }

    return colors.get(method, "#111111")


def build_method_message_html(method):
    """
    화면 표시용 HTML 문구입니다.
    XX와 입니다 사이에 한 칸을 둡니다.
    XX는 볼드체와 색상을 적용합니다.
    """
    color = get_method_color(method)

    if method == "인센티브":
        return (
            f"적용 계산 방식은 "
            f"<strong style='color:{color};'>{method}</strong>"
            f" 입니다. 오늘도 화이팅입니다 화진 수석님"
        )

    return (
        f"적용 계산 방식은 "
        f"<strong style='color:{color};'>{method}</strong>"
        f" 입니다."
    )


def build_method_message_plain(method):
    """
    쪽지 전송용 일반 텍스트 문구입니다.
    HTML 태그 없이 저장합니다.
    """
    if method == "인센티브":
        return f"적용 계산 방식은 {method} 입니다. 오늘도 화이팅입니다 화진 수석님"

    return f"적용 계산 방식은 {method} 입니다."


# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "result_html" not in st.session_state:
    st.session_state.result_html = ""

if "result_text" not in st.session_state:
    st.session_state.result_text = ""

if "sms_text" not in st.session_state:
    st.session_state.sms_text = ""

if "show_message_form" not in st.session_state:
    st.session_state.show_message_form = False

if "generated_message" not in st.session_state:
    st.session_state.generated_message = ""

if "message_generated" not in st.session_state:
    st.session_state.message_generated = False

if "calculation_formula_text" not in st.session_state:
    st.session_state.calculation_formula_text = ""


# -----------------------------
# 입력 영역
# -----------------------------
product_code = st.text_input(
    "상품코드 입력",
    max_chars=15
)

days = st.number_input(
    "상품 날짜 수 입력",
    min_value=0,
    step=1,
    value=9
)

people = st.number_input(
    "인솔자 제외 인원수",
    min_value=0,
    step=1,
    value=0
)

meal_excluded_count = st.number_input(
    "식사 불포함 횟수 입력",
    min_value=0,
    step=1,
    value=0
)

use_balkan = st.checkbox("발칸 계산 식을 사용하시겠습니까?")

balkan_12000_days = 0
balkan_16000_days = 0

if use_balkan:
    balkan_12000_days = st.number_input(
        "12,000원 적용 일수",
        min_value=0,
        step=1,
        value=0
    )

    balkan_16000_days = st.number_input(
        "16,000원 적용 일수",
        min_value=0,
        step=1,
        value=0
    )

praha_tour = st.checkbox("프라하 야간투어 스페셜 포함 상품인가요?")
vienna_concert = st.checkbox("비엔나 음악회 스페셜 포함 상품인가요?")
early_departure = st.checkbox("출발편 비행기 탑승 시간이 05:59 이전인가요?")
star_leader = st.checkbox("스타 인솔자 상품인가요?")


# -----------------------------
# 입력값 검증 함수
# -----------------------------
def validate_inputs(
    product_code,
    days,
    people,
    use_balkan,
    balkan_12000_days,
    balkan_16000_days
):
    """
    계산 전 입력값을 검증합니다.
    문제가 있으면 오류 메시지를 반환하고,
    문제가 없으면 None을 반환합니다.
    """

    if len(product_code.strip()) != 15:
        return "상품코드는 반드시 15자리로 입력해주세요."

    if days <= 0:
        return "상품 날짜 수가 0일입니다. 상품 날짜 수를 1일 이상으로 입력해주세요."

    if people <= 0:
        return "인솔자 제외 인원수가 0명입니다. 인솔자 제외 인원수를 1명 이상으로 입력해주세요."

    if use_balkan:
        total_balkan_days = balkan_12000_days + balkan_16000_days

        if total_balkan_days != days:
            return (
                f"발칸 적용 일수 합계가 상품 날짜 수와 다릅니다. "
                f"현재 발칸 적용 일수 합계는 {total_balkan_days}일이고, "
                f"상품 날짜 수는 {days}일입니다."
            )

    return None


# -----------------------------
# 계산 함수
# -----------------------------
def calculate_main_fee(
    product_code,
    days,
    people,
    use_balkan,
    balkan_12000_days,
    balkan_16000_days
):
    """
    메인 출장비 계산 함수입니다.
    계산 우선순위:
    1. 인센티브
    2. 스페인일주
    3. 발칸
    4. 일반

    단, 인솔자 제외 인원수가 15명 이하이면 15명으로 적용합니다.
    """

    applied_people = get_applied_people(people)
    premium = is_premium(product_code)

    # 1. 인센티브
    if is_incentive(product_code):
        main_amount = 250000 * days
        main_formula = f"250,000원 * {days}일"
        method = "인센티브"
        spain_premium_exception = False

        return {
            "amount": main_amount,
            "formula": main_formula,
            "method": method,
            "spain_premium_exception": spain_premium_exception,
            "applied_people": applied_people
        }

    # 2. 스페인일주
    if is_spain(product_code):
        if premium:
            main_amount = 200000 * days
            main_formula = f"200,000원 * {days}일"
        else:
            main_amount = 150000 * days
            main_formula = f"150,000원 * {days}일"

        method = "스페인일주"
        spain_premium_exception = True

        return {
            "amount": main_amount,
            "formula": main_formula,
            "method": method,
            "spain_premium_exception": spain_premium_exception,
            "applied_people": applied_people
        }

    # 3. 발칸
    if use_balkan:
        amount_12000 = 12000 * applied_people * balkan_12000_days
        amount_16000 = 16000 * applied_people * balkan_16000_days
        main_amount = amount_12000 + amount_16000

        formula_parts = []

        if balkan_12000_days > 0:
            formula_parts.append(
                f"12,000원 * {applied_people}명 * {balkan_12000_days}일"
            )

        if balkan_16000_days > 0:
            formula_parts.append(
                f"16,000원 * {applied_people}명 * {balkan_16000_days}일"
            )

        main_formula = " + ".join(formula_parts)
        method = "발칸"
        spain_premium_exception = False

        return {
            "amount": main_amount,
            "formula": main_formula,
            "method": method,
            "spain_premium_exception": spain_premium_exception,
            "applied_people": applied_people
        }

    # 4. 일반
    main_amount = 13000 * applied_people * days
    main_formula = f"{days}일 * {applied_people}명 * 13,000원"
    method = "일반"
    spain_premium_exception = False

    return {
        "amount": main_amount,
        "formula": main_formula,
        "method": method,
        "spain_premium_exception": spain_premium_exception,
        "applied_people": applied_people
    }


def calculate_sub_fee(
    product_code,
    meal_excluded_count,
    praha_tour,
    vienna_concert,
    early_departure,
    star_leader,
    spain_premium_exception
):
    """
    서브 출장비 계산 함수입니다.
    모든 방식에 공통 적용합니다.
    단, 스페인일주 프리미엄은 메인식에서 이미 처리하므로 별도 프리미엄 200,000원을 추가하지 않습니다.
    """

    sub_amount = 0
    sub_formula_parts = []

    # 프리미엄 추가
    if is_premium(product_code) and not spain_premium_exception:
        sub_amount += 200000
        sub_formula_parts.append("프리미엄 200,000원")

    # 식사 불포함
    if meal_excluded_count > 0:
        meal_amount = 30000 * meal_excluded_count
        sub_amount += meal_amount
        sub_formula_parts.append(
            f"식사불포함 {meal_excluded_count}회 {format_won(meal_amount)}"
        )

    # 프라하 야간투어
    if praha_tour:
        sub_amount += 70000
        sub_formula_parts.append("프라하야간투어 70,000원")

    # 비엔나 음악회
    if vienna_concert:
        sub_amount += 70000
        sub_formula_parts.append("비엔나음악회 70,000원")

    # 출발편 05:59 이전
    if early_departure:
        sub_amount += 50000
        sub_formula_parts.append("출발편 05:59 이전 50,000원")

    # 스타 인솔자
    if star_leader:
        sub_amount += 300000
        sub_formula_parts.append("스타 인솔자 300,000원")

    return {
        "amount": sub_amount,
        "formula_parts": sub_formula_parts
    }


# -----------------------------
# 결과 문구 생성 함수
# -----------------------------
def build_formula_text_plain(main_formula, sub_formula_parts):
    """
    쪽지 전송용 계산식을 생성합니다.
    메인 계산식과 서브 계산식을 각각 괄호로 감싸서 표시합니다.
    """

    formula_parts = []

    main_parts = main_formula.split(" + ")

    for part in main_parts:
        formula_parts.append(f"({part})")

    for part in sub_formula_parts:
        formula_parts.append(f"({part})")

    return " + ".join(formula_parts)


def build_formula_text_html(main_formula, sub_formula_parts):
    """
    화면 표시용 계산식을 생성합니다.
    메인 계산식과 서브 계산식을 각각 괄호로 감싸서 표시합니다.
    """

    formula_parts = []

    main_parts = main_formula.split(" + ")

    for part in main_parts:
        formula_parts.append(f"({html.escape(part)})")

    for part in sub_formula_parts:
        formula_parts.append(f"({html.escape(part)})")

    return " + ".join(formula_parts)


def build_result_text_plain(
    method,
    main_formula,
    sub_formula_parts,
    total_amount,
    people_adjustment_text
):
    """
    쪽지 전송용 일반 텍스트 결과 문구입니다.
    """

    method_message = build_method_message_plain(method)
    formula_text = build_formula_text_plain(main_formula, sub_formula_parts)

    if people_adjustment_text:
        result_text = (
            f"{method_message}\n"
            f"{people_adjustment_text}\n\n"
            f"출장비 계산 : {formula_text} = {format_won(total_amount)}"
        )
    else:
        result_text = (
            f"{method_message}\n\n"
            f"출장비 계산 : {formula_text} = {format_won(total_amount)}"
        )

    return result_text


def build_calculation_formula_text(main_formula, sub_formula_parts, total_amount):
    """
    인솔자 쪽지 전문에 들어갈 계산식 전용 문구입니다.
    """

    formula_text = build_formula_text_plain(main_formula, sub_formula_parts)

    return f"{formula_text} = {format_won(total_amount)}"


def build_result_html(
    method,
    main_formula,
    sub_formula_parts,
    total_amount,
    people_adjustment_text
):
    """
    화면 표시용 HTML 결과 문구입니다.
    보정 안내 문구에서 HTML 코드가 노출되지 않도록 한 줄 문자열로 조립합니다.
    """

    method_message_html = build_method_message_html(method)
    formula_text = build_formula_text_html(main_formula, sub_formula_parts)

    adjustment_html = ""

    if people_adjustment_text:
        adjustment_html = (
            f"<div style='margin-top:4px;'>"
            f"{html.escape(people_adjustment_text)}"
            f"</div>"
        )

    result_html = (
        "<div style='"
        "background-color:#EAF7EA;"
        "border:1px solid #B7E0B7;"
        "border-radius:8px;"
        "padding:16px;"
        "color:#111111;"
        "line-height:1.7;"
        "font-size:16px;"
        "'>"
        f"<div>{method_message_html}</div>"
        f"{adjustment_html}"
        "<br>"
        f"<div>출장비 계산 : {formula_text} = <strong>{format_won(total_amount)}</strong></div>"
        "</div>"
    )

    return result_html


def build_message_display_html(message):
    """
    인솔자 쪽지 전문을 화면에 표시할 HTML로 변환합니다.
    특정 기호로 시작하는 줄은 볼드체로 표시합니다.
    """

    bold_prefixes = (
        "■",
        "♧",
        "◐",
        "★",
        "※"
    )

    html_lines = []

    for line in message.split("\n"):
        escaped_line = html.escape(line)

        if line.strip().startswith(bold_prefixes):
            html_lines.append(f"<strong>{escaped_line}</strong>")
        else:
            html_lines.append(escaped_line)

    return "<br>".join(html_lines)


def normalize_blank_lines(text):
    """
    연속된 빈 줄을 한 줄로 줄입니다.
    즉, 두 줄 이상 비어 있는 공란은 한 줄 공란으로 정리합니다.
    """

    lines = text.split("\n")
    normalized_lines = []
    blank_count = 0

    for line in lines:
        if line.strip() == "":
            blank_count += 1

            if blank_count <= 1:
                normalized_lines.append("")
        else:
            blank_count = 0
            normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


# -----------------------------
# 계산 실행
# -----------------------------
if st.button("계산하기"):
    validation_error = validate_inputs(
        product_code=product_code,
        days=days,
        people=people,
        use_balkan=use_balkan,
        balkan_12000_days=balkan_12000_days,
        balkan_16000_days=balkan_16000_days
    )

    if validation_error:
        st.error(validation_error)
        st.session_state.result_html = ""
        st.session_state.result_text = ""
        st.session_state.sms_text = ""
        st.session_state.show_message_form = False
        st.session_state.generated_message = ""
        st.session_state.message_generated = False
        st.session_state.calculation_formula_text = ""
    else:
        main_result = calculate_main_fee(
            product_code=product_code,
            days=days,
            people=people,
            use_balkan=use_balkan,
            balkan_12000_days=balkan_12000_days,
            balkan_16000_days=balkan_16000_days
        )

        sub_result = calculate_sub_fee(
            product_code=product_code,
            meal_excluded_count=meal_excluded_count,
            praha_tour=praha_tour,
            vienna_concert=vienna_concert,
            early_departure=early_departure,
            star_leader=star_leader,
            spain_premium_exception=main_result["spain_premium_exception"]
        )

        total_amount = main_result["amount"] + sub_result["amount"]

        applied_people = main_result["applied_people"]

        people_adjustment_text = build_people_adjustment_text(
            original_people=people,
            applied_people=applied_people
        )

        result_html = build_result_html(
            method=main_result["method"],
            main_formula=main_result["formula"],
            sub_formula_parts=sub_result["formula_parts"],
            total_amount=total_amount,
            people_adjustment_text=people_adjustment_text
        )

        result_text = build_result_text_plain(
            method=main_result["method"],
            main_formula=main_result["formula"],
            sub_formula_parts=sub_result["formula_parts"],
            total_amount=total_amount,
            people_adjustment_text=people_adjustment_text
        )

        calculation_formula_text = build_calculation_formula_text(
            main_formula=main_result["formula"],
            sub_formula_parts=sub_result["formula_parts"],
            total_amount=total_amount
        )

        st.session_state.result_html = result_html
        st.session_state.result_text = result_text
        st.session_state.sms_text = result_text
        st.session_state.show_message_form = False
        st.session_state.generated_message = ""
        st.session_state.message_generated = False
        st.session_state.calculation_formula_text = calculation_formula_text


# -----------------------------
# 결과 표시
# -----------------------------
if st.session_state.result_html:
    st.subheader("계산 결과")
    st.markdown(st.session_state.result_html, unsafe_allow_html=True)

    st.markdown(
        "<div style='height:16px;'></div>",
        unsafe_allow_html=True
    )


# -----------------------------
# 인솔자 쪽지 양식 작성
# -----------------------------
if st.session_state.sms_text:
    if st.button("인솔자 쪽지 양식 작성"):
        st.session_state.show_message_form = True
        st.session_state.message_generated = False

if st.session_state.show_message_form:
    st.subheader("인솔자 쪽지 양식 작성")

    manager_name = st.text_input(
        "상품 담당자 이름"
    )

    visit_praha = st.checkbox(
        "프라하를 방문하는 상품인가요?"
    )

    visit_hallstatt = st.checkbox(
        "할슈타트를 방문하는 상품인가요?"
    )

    queen_direct_payment = st.checkbox(
        "인솔자에게 퀸투어 직불금이 전달되는 상품인가요?"
    )

    if st.button("실행"):
        queen_direct_payment_text = ""

        if queen_direct_payment:
            queen_direct_payment_text = """※퀸투어 진행상품으로 직불금 2000유로 있습니다.

첨부된 직불금내역서 출력하셔서 지정된 날짜에 11층 자금 지원팀서 수령 부탁드립니다. 
"""

        praha_text = ""

        if visit_praha:
            praha_text = """■  체코 영문 여행자 보험 증서

체코에서 여행자와 불법이민자 구분을 여행자보험 증서로 확인한다 하니 고객분들에게 1부씩 전달 바랍니다.

보험 시스템 문제로 영문 보험증서 한정 인솔자님 영문성 제외되며, 국문 정상 반영되어 보험 문제 없는 점 참조 바랍니다.

===============================================================
"""

        hallstatt_text = ""

        if visit_hallstatt:
            hallstatt_text = """★ 할슈타트 내 행사 진행 시에는 멘트는 꼭 버스 안에서만 진행해 주시고, 야외에서는 자유 일정으로 진행 부탁드립니다. 야외에서의 가이드 행위가 엄격히 금지되어 있는 지역으로, 가이드 분들이 현지 경찰에 인계되는 사례가 종종 발생하고 있습니다.
"""

        final_message = f"""인솔자님 안녕하세요, 하나투어 유럽상품1팀 {manager_name.strip()} 입니다 :)

{product_code.strip()} 상품 행사 관련 서류 전달드립니다.

FNL 확정서 식당까지 모두 확정되어, 확정일정표 반영해두었습니다. 한글일정표 인쇄 이상없습니다.

{queen_direct_payment_text}
===============================================================

■ 행사 특이사항

- 선택관광 선포함자는 총 n명입니다. 

nnn, nnn 님.

- 현지서비스 :  

nnn 님 초콜릿 1개 <멘트 : >

총 : 초콜릿 1개

■ 기타 특이사항

- 

===============================================================

{praha_text}

■ 출장비 안내

♧ 출장비 내역 꼼꼼히 확인 바라며, 출장비는 출발 당일 오전 팀장님 결재가 진행되니 참조 바랍니다.

♧ 출장비 계산 값은 아래와 같으며, 아래 비용에서 세금 3.3%를 제외한 금액이 입금됩니다.

출장비 계산 : {st.session_state.calculation_formula_text}

================================================================================

■ 공통 서류 안내

현지 행사 진행 시 불가피한 상황으로 면책 동의서, 일정 변경 동의서, 안전사고 매뉴얼, 비상상황 대응 매뉴얼 등에 대한

확인이 필요한 경우 아래 링크를 통해 매뉴얼 지침 출발 전 사전 확인바랍니다. | 다운로드 가능

특히, 일정 순서를 변경하게 되면 일정 변경 동의서를 꼭 받아 귀책 사유가 되지 않도록 주의하시기 바랍니다.

https://drive.google.com/drive/folders/1Tf_4RBZMWziPzlJBWKOim4HfNWok-4L6?usp=sharing

■ 하나투어 여행 개런티 프로그램

일정에 없는 쇼핑, 선택관광, 가이드/기사 경비 지불시 100% 전액 환불 되는 프로그램입니다.

https://www.hanatour.com/promotion/plan/PM006682D66D

개런티 프로그램 숙지 하셔서 일정표에 없는 쇼핑, 선택관광, 팁 요구 등이 발생하지 않도록 주의 바랍니다.

■ 자유 시간 엄수

일정표에 있는 자유 시간은 10~20분 차이가 나더라도 진행 되게 끔 꼭 지켜 주셔야 합니다.

현지 사정에 의해 자유 시간이 줄어들 경우 모든 고객이 인지 할 수 있도록 사전 설명 바랍니다. 

◐ 행사 시 유의 사항 ◑

■ 수신기

출장 전날 문자로 수령 안내가 온다고 합니다.  

분실시 개당 €100 발생되며 분실 비용은 현장 수령하시어 귀국 후 수신기 반납 시 전달하시면 됩니다. 

관련된 주의사항과 분실 비용은 고객분들에게 사전 고지 후 관리 당부 바랍니다.

■ 고객 여권/영문보험증서 지참 확인

■ 호텔 객실 키 추가 반출 금지

현지에서 도둑이 카운터에서 호텔 객실키를 발급 받아 객실로 침입한 사례가 발생했습니다.

프론트 체크인 시 절대객실 키 추가 반출되지 않도록 주의 주시기 바랍니다.

손님들께는 번거로우시겠지만 객실키는 위와 같은 문제로 개별적으로 추가 생성은 불가한 점 안내 바랍니다.

■ 인솔자님께서 하나투어 일정표와 현지 확정서가 동일한 지 꼭 꼼꼼하게 재확인 하셔야만 합니다.

작은 실수가 큰 손해로 이어지지 않도록, 확정표 상 이상하다고 생각되시는 부분 있으시면 꼭 문의 하시고 사전 확인 바랍니다.

{hallstatt_text}

항상 현장에서 고군분투 해 주시는 인솔자님께 감사드립니다.

이번 팀도 행사 잘 진행 부탁 드리겠습니다."""

        final_message = normalize_blank_lines(final_message)

        st.session_state.generated_message = final_message
        st.session_state.message_generated = True

if st.session_state.message_generated:
    st.success("인솔자 쪽지 양식이 생성되었습니다.")

    st.markdown(
        """
        <h2 style="
            font-size: 30px;
            font-weight: 800;
            color: #1f2937;
            margin-top: 24px;
            margin-bottom: 24px;
        ">
            생성된 인솔자 쪽지 전문
        </h2>
        """,
        unsafe_allow_html=True
    )

    message_for_js = json.dumps(st.session_state.generated_message)
    display_html = build_message_display_html(st.session_state.generated_message)

    components.html(
        f"""
        <div>
            <button
                id="copyButton"
                style="
                    background-color:#ff4b4b;
                    color:white;
                    border:none;
                    border-radius:8px;
                    padding:10px 18px;
                    font-size:15px;
                    font-weight:700;
                    margin-bottom:12px;
                    cursor:pointer;
                "
            >
                복사하기
            </button>

            <span
                id="copyStatus"
                style="
                    margin-left:10px;
                    color:#16a34a;
                    font-size:14px;
                    font-weight:600;
                "
            ></span>

            <div style="
                border:1px solid #999999;
                background-color:#ffffff;
                padding:12px;
                width:100%;
                height:520px;
                overflow:auto;
                white-space:normal;
                font-family:Arial, sans-serif;
                font-size:14px;
                line-height:1.65;
                box-sizing:border-box;
            ">
                {display_html}
            </div>
        </div>

        <script>
            const copyButton = document.getElementById("copyButton");
            const copyStatus = document.getElementById("copyStatus");
            const messageText = {message_for_js};

            copyButton.addEventListener("click", async function() {{
                try {{
                    await navigator.clipboard.writeText(messageText);
                    copyStatus.innerText = "복사되었습니다.";
                }} catch (err) {{
                    const textArea = document.createElement("textarea");
                    textArea.value = messageText;
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();

                    try {{
                        document.execCommand("copy");
                        copyStatus.innerText = "복사되었습니다.";
                    }} catch (copyErr) {{
                        copyStatus.innerText = "복사 실패. 직접 드래그해서 복사해주세요.";
                    }}

                    document.body.removeChild(textArea);
                }}
            }});
        </script>
        """,
        height=620
    )


# -----------------------------
# 패치노트
# -----------------------------
st.markdown("---")

with st.expander("ver 1.1.0.1 패치노트 보기"):
    st.markdown("""
1. 패치노트를 확인할 수 있는 기능을 추가했습니다.
2. 발칸 계산 방식을 적용하는 법을 자동에서 수동으로 변경했습니다.
3. 인센티브 계산 식을 추가했습니다.
4. 인솔자 쪽지 내에 퀸투어 직불금 관련 내용을 추가할 수 있게 변경했습니다.
5. 기타 비주얼 업데이트들을 적용했습니다.

오늘도 화이팅입니당:D
""")
